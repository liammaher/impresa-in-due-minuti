//go:build !windows

package main

import (
	"bufio"
	"encoding/json"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/lovincyrus/personal-vault/internal/vault"
)

// setupRun is 'pvault setup --no-browser' on VAULT_DIR, with the page's address.
type setupRun struct {
	cmd    *exec.Cmd
	origin string
	out    *strings.Builder
	done   chan struct{}
}

func startSetup(t *testing.T, bin string, env []string, args ...string) *setupRun {
	t.Helper()
	cmd := exec.Command(bin, append([]string{"setup", "--no-browser"}, args...)...)
	cmd.Env = env
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		t.Fatal(err)
	}
	if err := cmd.Start(); err != nil {
		t.Fatal(err)
	}
	r := &setupRun{cmd: cmd, out: &strings.Builder{}, done: make(chan struct{})}
	lines, first := bufio.NewScanner(stdout), make(chan string, 1)
	go func() {
		for lines.Scan() {
			line := lines.Text()
			r.out.WriteString(line + "\n")
			if strings.HasPrefix(line, "Open this page in the browser: ") {
				first <- strings.TrimSuffix(strings.TrimPrefix(line, "Open this page in the browser: "), "/")
			}
		}
		cmd.Wait()
		close(r.done)
	}()
	t.Cleanup(func() { cmd.Process.Kill(); <-r.done })
	select {
	case r.origin = <-first:
	case <-time.After(10 * time.Second):
		t.Fatal("pvault setup printed no address")
	}
	return r
}

func (r *setupRun) post(t *testing.T, path, origin, ctype string, body any) (int, map[string]any) {
	t.Helper()
	b, _ := json.Marshal(body)
	req, _ := http.NewRequest("POST", r.origin+path, strings.NewReader(string(b)))
	req.Header.Set("Content-Type", ctype)
	if origin != "" {
		req.Header.Set("Origin", origin)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	var out map[string]any
	json.NewDecoder(resp.Body).Decode(&out)
	return resp.StatusCode, out
}

func (r *setupRun) state(t *testing.T) setupState {
	t.Helper()
	resp, err := http.Get(r.origin + "/state")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	var st setupState
	json.NewDecoder(resp.Body).Decode(&st)
	return st
}

func (r *setupRun) finish(t *testing.T) string {
	t.Helper()
	if code, _ := r.post(t, "/done", r.origin, "application/json", nil); code != 200 {
		t.Fatalf("/done: %d", code)
	}
	select {
	case <-r.done:
	case <-time.After(10 * time.Second):
		t.Fatal("pvault setup didn't exit after /done")
	}
	return r.out.String()
}

// The vault made, opened and shown without a terminal: the setup page creates
// it with the typed password, shows the secret key once, and opens a locked
// one; other pages, Hosts and bodies are refused, and nothing secret is printed.
func TestSetup_CreatesAndOpensWithoutTerminal(t *testing.T) {
	dir := shortVaultDir(t)
	bin := buildPvault(t, true)
	l, _ := net.Listen("tcp", "127.0.0.1:0")
	port := l.Addr().(*net.TCPAddr).Port
	l.Close()
	env := append(os.Environ(), "VAULT_DIR="+dir, "VAULT_PORT="+strconv.Itoa(port), "VAULT_ADDR=http://127.0.0.1:"+strconv.Itoa(port))
	t.Cleanup(func() { exec.Command(bin, "lock").Run() })
	lock := exec.Command(bin, "lock")
	lock.Env = env

	r := startSetup(t, bin, env, "--impresa")
	resp, err := http.Get(r.origin + "/")
	if err != nil {
		t.Fatal(err)
	}
	resp.Body.Close()
	if csp := resp.Header.Get("Content-Security-Policy"); !strings.Contains(csp, "default-src 'none'") || !strings.Contains(csp, "sha256-") {
		t.Fatalf("CSP %q", csp)
	}
	if st := r.state(t); st.Exists || st.Unlocked {
		t.Fatalf("state before create: %+v", st)
	}
	good := map[string]string{"password": "password-1", "confirm": "password-1"}
	for _, c := range []struct{ origin, ctype string }{
		{"", "application/json"},                    // no Origin: not this page
		{"http://evil.example", "application/json"}, // another page
		{r.origin, "text/plain"},                    // a form any page can send
	} {
		if code, _ := r.post(t, "/create", c.origin, c.ctype, good); code != http.StatusForbidden {
			t.Fatalf("create from %q as %q: %d, want 403", c.origin, c.ctype, code)
		}
	}
	rebind, _ := http.NewRequest("GET", r.origin+"/state", nil)
	rebind.Host = "evil.example"
	if resp, err := http.DefaultClient.Do(rebind); err != nil || resp.StatusCode != http.StatusForbidden {
		t.Fatalf("a rebinding Host was served: %v %v", resp, err)
	}
	if code, out := r.post(t, "/create", r.origin, "application/json", map[string]string{"password": "short", "confirm": "short"}); code != 400 || !strings.Contains(out["error"].(string), "8 caratteri") {
		t.Fatalf("short password: %d %v", code, out)
	}
	if code, _ := r.post(t, "/create", r.origin, "application/json", map[string]string{"password": "password-1", "confirm": "password-2"}); code != 400 {
		t.Fatalf("mismatched confirmation: %d", code)
	}
	code, out := r.post(t, "/create", r.origin, "application/json", good)
	if code != 200 {
		t.Fatalf("create: %d %v", code, out)
	}
	key, _ := out["secret_key"].(string)
	saved, _ := os.ReadFile(filepath.Join(dir, "secret.key"))
	if key == "" || strings.TrimSpace(string(saved)) != key {
		t.Fatalf("secret key shown %q, saved %q", key, saved)
	}
	if st := r.state(t); !st.Exists || !st.Unlocked || !st.HasPassword {
		t.Fatalf("state after create: %+v", st)
	}
	if code, _ := r.post(t, "/create", r.origin, "application/json", good); code != http.StatusConflict {
		t.Fatalf("a second create: %d", code)
	}
	printed := r.finish(t)
	if strings.Contains(printed, key) || strings.Contains(printed, "password-1") {
		t.Fatalf("setup printed a secret:\n%s", printed)
	}
	if !strings.Contains(printed, "Vault: created") || !strings.Contains(printed, "Open: true") {
		t.Fatalf("setup printed:\n%s", printed)
	}

	// Locked again: the page opens it with the password, and refuses a wrong one.
	if out, err := lock.CombinedOutput(); err != nil {
		t.Fatalf("lock: %v\n%s", err, out)
	}
	r = startSetup(t, bin, env)
	if st := r.state(t); !st.Exists || st.Unlocked || st.HasPassword {
		t.Fatalf("state when locked: %+v", st)
	}
	if code, _ := r.post(t, "/approvals", r.origin, "application/json", nil); code != http.StatusConflict {
		t.Fatalf("approvals before any password: %d", code)
	}
	if code, out := r.post(t, "/open", r.origin, "application/json", map[string]string{"password": "wrong-password"}); code != 401 || !strings.Contains(out["error"].(string), "non è giusta") {
		t.Fatalf("wrong password: %d %v", code, out)
	}
	if code, out := r.post(t, "/open", r.origin, "application/json", map[string]string{"password": "password-1"}); code != 200 {
		t.Fatalf("open: %d %v", code, out)
	}
	if st := r.state(t); !st.Unlocked {
		t.Fatalf("state after open: %+v", st)
	}
	if printed := r.finish(t); !strings.Contains(printed, "Open: true") || strings.Contains(printed, "password-1") {
		t.Fatalf("setup printed:\n%s", printed)
	}
}

// Five wrong passwords close the page: it can't be used to guess.
func TestSetup_TooManyWrongPasswordsCloses(t *testing.T) {
	dir := shortVaultDir(t)
	bin := buildPvault(t, true)
	cmd := exec.Command(bin, "lock")
	cmd.Env = append(os.Environ(), "VAULT_DIR="+dir)
	t.Cleanup(func() { cmd.Run() })
	if _, err := vault.Init(dir, "test-password"); err != nil {
		t.Fatal(err)
	}
	r := startSetup(t, bin, append(os.Environ(), "VAULT_DIR="+dir))
	for i := 0; i < setupMaxFailures; i++ {
		r.post(t, "/open", r.origin, "application/json", map[string]string{"password": "wrong-" + strconv.Itoa(i)})
	}
	select {
	case <-r.done:
	case <-time.After(10 * time.Second):
		t.Fatal("the page stayed open after five wrong passwords")
	}
}
