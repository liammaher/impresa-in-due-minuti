package main

import (
	"crypto/sha256"
	_ "embed"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"sync"
	"time"

	"github.com/lovincyrus/personal-vault/internal/vault"
)

const setupUsage = `usage: pvault [--vault <name>] setup [--impresa] [--no-browser]
  Opens a page in the browser where the person creates the vault (or opens a
  locked one), keeps its recovery key and turns on Touch ID or Windows Hello,
  all without a terminal. Waits until they are done (at most 15 minutes), then
  prints what is ready. Nothing secret is printed.
  --impresa: a new vault is a business vault (a studio and its clients).
  --no-browser: print the page's address instead of opening it.`

// The setup page: served by this command, not by the vault server, because
// before it there may be no vault and no server at all.
//
//go:embed setup.html
var setupHTML []byte

// setupCSP: the page runs only its own inline script and style (by hash) and
// talks only to this command, as the onboarding page does (pageCSP).
var setupCSP = func() string {
	hash := func(tag string) string {
		m := regexp.MustCompile(`(?s)<` + tag + `>(.*?)</` + tag + `>`).FindSubmatch(setupHTML)
		if m == nil {
			panic("setup page has no inline <" + tag + ">")
		}
		sum := sha256.Sum256(m[1])
		return "'sha256-" + base64.StdEncoding.EncodeToString(sum[:]) + "'"
	}
	return "default-src 'none'; script-src " + hash("script") + "; style-src " + hash("style") +
		"; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
}()

const (
	setupWait        = 15 * time.Minute
	setupMaxFailures = 5
)

func cmdSetup() {
	kind, browser := "", true
	for _, arg := range os.Args[2:] {
		switch {
		case arg == "--impresa" && kind == "":
			kind = vault.KindImpresa
		case arg == "--no-browser" && browser:
			browser = false
		default:
			fatal(setupUsage)
		}
	}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		fatal("setup page: %v", err)
	}
	s := newSetup(vaultDir(), kind, fmt.Sprintf("http://127.0.0.1:%d", ln.Addr().(*net.TCPAddr).Port))
	srv := &http.Server{Handler: s, ReadHeaderTimeout: 10 * time.Second}
	go srv.Serve(ln)
	if browser && openBrowser(s.origin+"/") {
		fmt.Println("Opened the setup page in the browser: the person types their password there, never here.")
	} else {
		fmt.Printf("Open this page in the browser: %s/\n", s.origin)
	}
	fmt.Println("Waiting until they are done…")
	select {
	case <-s.done:
	case <-time.After(setupWait):
		fmt.Println("The setup page closed after 15 minutes.")
	}
	srv.Close()
	s.forget()
	st := s.state()
	fmt.Printf("Vault: %s\n", map[bool]string{true: "created", false: "not created"}[st.Exists])
	if st.Exists {
		fmt.Printf("Open: %v\n", st.Unlocked)
		fmt.Printf("%s: %s\n", st.ApproverName, map[bool]string{true: "on", false: "off"}[st.ApproverOn])
	}
}

// setup is one run of the setup page. It holds the password the person typed
// (create or open) until the page is done, so turning on Touch ID or Hello
// needs no second typing; forget clears it.
type setup struct {
	dir, kind, origin string
	mu                sync.Mutex
	pw                []byte
	failures          int
	done              chan struct{}
	finish            sync.Once
}

func newSetup(dir, kind, origin string) *setup {
	return &setup{dir: dir, kind: kind, origin: origin, done: make(chan struct{})}
}

func (s *setup) end() { s.finish.Do(func() { close(s.done) }) }

func (s *setup) forget() {
	s.mu.Lock()
	defer s.mu.Unlock()
	clear(s.pw)
	s.pw = nil
}

type setupState struct {
	Exists       bool   `json:"exists"`
	Unlocked     bool   `json:"unlocked"`
	Approver     string `json:"approver"` // touchid, hello, or "" where neither exists
	ApproverName string `json:"approver_name"`
	CanApprove   bool   `json:"can_approve"` // the approver is installed and can be turned on
	ApproverOn   bool   `json:"approver_on"`
	HasPassword  bool   `json:"has_password"` // typed on this page already
}

func (s *setup) state() setupState {
	var st setupState
	_, err := os.Stat(filepath.Join(s.dir, "vault.db"))
	st.Exists = err == nil
	st.Unlocked = st.Exists && isVaultUnlocked() && checkVaultServer() == nil
	switch runtime.GOOS {
	case "darwin":
		st.Approver, st.ApproverName = "touchid", "Touch ID"
		touchIDCached = nil // enrolling on this page changes it
		info := touchIDStatus()
		st.CanApprove, st.ApproverOn = info.helper != "", info.enrolled
	case "windows":
		st.Approver, st.ApproverName = "hello", "Windows Hello"
		st.CanApprove = true
		st.ApproverOn = st.Unlocked && verifiedApprover == "hello"
	default:
		st.ApproverName = "Approvals"
	}
	s.mu.Lock()
	st.HasPassword = s.pw != nil
	s.mu.Unlock()
	return st
}

func (s *setup) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("Referrer-Policy", "no-referrer")
	// A DNS-rebinding page reaches 127.0.0.1 under its own name: only a
	// loopback Host is this page.
	host := r.Host
	if h, _, err := net.SplitHostPort(host); err == nil {
		host = h
	}
	if host != "127.0.0.1" && host != "localhost" {
		http.Error(w, "requests must use 127.0.0.1", http.StatusForbidden)
		return
	}
	if r.Method == http.MethodGet {
		switch r.URL.Path {
		case "/":
			w.Header().Set("Content-Type", "text/html; charset=utf-8")
			w.Header().Set("Content-Security-Policy", setupCSP)
			w.Write(setupHTML)
		case "/state":
			setupJSON(w, http.StatusOK, s.state())
		default:
			http.NotFound(w, r)
		}
		return
	}
	// Another web page can't send JSON here without a CORS preflight this
	// never grants, and the browser names the page that sends: only this one.
	if r.Method != http.MethodPost || !strings.HasPrefix(r.Header.Get("Content-Type"), "application/json") ||
		r.Header.Get("Origin") != s.origin {
		http.Error(w, "forbidden", http.StatusForbidden)
		return
	}
	var body struct {
		Password string `json:"password"`
		Confirm  string `json:"confirm"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4096)).Decode(&body); err != nil && r.URL.Path != "/approvals" && r.URL.Path != "/done" {
		setupError(w, http.StatusBadRequest, "La richiesta non è valida.")
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	switch r.URL.Path {
	case "/create":
		s.create(w, body.Password, body.Confirm)
	case "/open":
		s.open(w, body.Password)
	case "/approvals":
		s.approvals(w)
	case "/done":
		setupJSON(w, http.StatusOK, map[string]bool{"ok": true})
		s.end()
	default:
		http.NotFound(w, r)
	}
}

// create makes the vault with the password typed on the page, starts its
// server open, and returns the secret key once, for the person to keep.
func (s *setup) create(w http.ResponseWriter, pw, confirm string) {
	if err := vault.CanInit(s.dir); err != nil {
		setupError(w, http.StatusConflict, "L'archivio esiste già: lo apra con la sua password.")
		return
	}
	if len(pw) < 8 {
		setupError(w, http.StatusBadRequest, "La password deve avere almeno 8 caratteri.")
		return
	}
	if pw != confirm {
		setupError(w, http.StatusBadRequest, "Le due password non coincidono.")
		return
	}
	sk, err := vault.InitWithOptions(s.dir, pw, vault.InitOptions{Kind: s.kind})
	if err != nil {
		setupError(w, http.StatusInternalServerError, "Non sono riuscito a creare l'archivio: "+err.Error())
		return
	}
	if _, err := ensurePort(s.dir); err != nil {
		setupError(w, http.StatusInternalServerError, "Archivio creato, ma non sono riuscito ad aprirlo: "+err.Error())
		return
	}
	if verified, err := startBackgroundServer(pw, sk); err != nil || !verified {
		setupJSON(w, http.StatusOK, map[string]any{"secret_key": sk, "warning": "Archivio creato; per aprirlo ricarichi la pagina."})
		s.pw = []byte(pw)
		return
	}
	s.pw = []byte(pw)
	setupJSON(w, http.StatusOK, map[string]string{"secret_key": sk})
}

// open checks the password and opens a locked vault (starting its server if
// it isn't running). On an open vault it only checks the password, which the
// page then uses to turn on Touch ID or Hello.
func (s *setup) open(w http.ResponseWriter, pw string) {
	sk, err := readSecretKey()
	if err != nil {
		setupError(w, http.StatusConflict, "Manca la chiave di recupero di questo archivio sul computer: "+err.Error())
		return
	}
	if err := checkCredentials(pw, sk); err != nil {
		s.failures++
		if s.failures >= setupMaxFailures {
			setupError(w, http.StatusUnauthorized, "Password sbagliata troppe volte: la pagina si chiude.")
			s.end()
			return
		}
		setupError(w, http.StatusUnauthorized, "La password non è giusta.")
		return
	}
	if !isVaultUnlocked() {
		if portHasVault() {
			if err := checkVaultServer(); err != nil {
				setupError(w, http.StatusConflict, "Sulla porta dell'archivio risponde un altro programma: "+err.Error())
				return
			}
			err = reUnlock(pw, sk)
		} else {
			removeStalePID()
			var verified bool
			verified, err = startBackgroundServer(pw, sk)
			if err == nil && !verified {
				err = errors.New("non risponde")
			}
		}
		if err != nil {
			setupError(w, http.StatusInternalServerError, "Non sono riuscito ad aprire l'archivio: "+err.Error())
			return
		}
	}
	s.pw = []byte(pw)
	setupJSON(w, http.StatusOK, map[string]bool{"ok": true})
}

// approvals turns on Touch ID (the helper saves the password behind the
// fingerprint) or Windows Hello (a session grant from the password, then
// POST /vault/hello over the private channel), with the password typed on the
// page. A caller that knew the password could do the same from a terminal.
func (s *setup) approvals(w http.ResponseWriter) {
	if s.pw == nil {
		setupError(w, http.StatusConflict, "Scriva prima la password dell'archivio.")
		return
	}
	switch runtime.GOOS {
	case "darwin":
		self, err := os.Executable()
		if err == nil {
			self, err = filepath.EvalSymlinks(self)
		}
		if err == nil {
			_, err = runTouchID(string(s.pw), "enroll", "--server", self)
		}
		if err != nil {
			setupError(w, http.StatusInternalServerError, "Touch ID non è stato attivato: "+err.Error())
			return
		}
	case "windows":
		sk, err := readSecretKey()
		if err == nil {
			cliToken, err = requestGrant(string(s.pw), sk, "2m")
		}
		if err == nil {
			var resp *http.Response
			if resp, err = apiRequest("POST", "/vault/hello", map[string]bool{"enabled": true}); err == nil {
				err = apiResult(resp, nil)
			}
		}
		cliToken = ""
		if err != nil {
			setupError(w, http.StatusInternalServerError, "Windows Hello non è stato attivato: "+err.Error())
			return
		}
	default:
		setupError(w, http.StatusNotImplemented, "Su questo sistema non c'è Touch ID né Windows Hello.")
		return
	}
	setupJSON(w, http.StatusOK, map[string]bool{"ok": true})
}

func setupJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func setupError(w http.ResponseWriter, status int, msg string) {
	setupJSON(w, status, map[string]string{"error": msg})
}
