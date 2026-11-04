package vault

import (
	"encoding/json"
	"os"
	"testing"
	"time"
)

// promptFixture is testdata/prompts.json, shared with the Touch ID helper's
// test (cmd/pvault/touchid_prompt_test.go).
type promptFixture struct {
	Grants []struct {
		Vault  string
		Scope  *string
		Access string
		TTL    int
		Want   string
	}
	Signs []struct {
		Vault, Name, Hash8, Requester, Want string
		Pages                               int
	}
	RefusedScopes  []string
	AcceptedScopes []string
	CategoryLabels map[string]string
}

func loadPromptFixture(t *testing.T) promptFixture {
	t.Helper()
	data, err := os.ReadFile("testdata/prompts.json")
	if err != nil {
		t.Fatal(err)
	}
	var f promptFixture
	if err := json.Unmarshal(data, &f); err != nil {
		t.Fatal(err)
	}
	return f
}

func fixtureLabel(vault string) string {
	if vault == "" {
		vault = ".pvault"
	}
	return PromptVaultLabel("/home/x/" + vault)
}

func TestGrantPrompt_Fixture(t *testing.T) {
	for _, c := range loadPromptFixture(t).Grants {
		ttl := c.TTL
		if ttl == 0 {
			ttl = 120
		}
		scope := ""
		if c.Scope != nil {
			scope = *c.Scope
		}
		got, err := GrantPrompt(fixtureLabel(c.Vault), scope, c.Access, time.Duration(ttl)*time.Second)
		if err != nil {
			t.Errorf("%+v: %v", c, err)
		} else if got != c.Want {
			t.Errorf("%+v:\n got  %q\n want %q", c, got, c.Want)
		}
	}
}

// Each schema category has its Italian name in prompts, the same the Touch ID
// helper uses (prompts.json categoryLabels).
func TestPromptCategories_Fixture(t *testing.T) {
	want := loadPromptFixture(t).CategoryLabels
	if len(want) != len(PromptCategories) {
		t.Fatalf("prompts.json names %d categories, PromptCategories %d", len(want), len(PromptCategories))
	}
	for c, l := range want {
		if PromptCategories[c] != l {
			t.Errorf("%s: PromptCategories says %q, prompts.json %q", c, PromptCategories[c], l)
		}
	}
	for _, c := range RecommendedSchema.Categories {
		if _, ok := PromptCategories[c.Name]; !ok {
			t.Errorf("schema category %s has no name in prompts", c.Name)
		}
	}
}

func TestSignPrompt_Fixture(t *testing.T) {
	for _, c := range loadPromptFixture(t).Signs {
		if got := SignPrompt(fixtureLabel(c.Vault), c.Name, c.Pages, c.Hash8, c.Requester, SignGrantTTL); got != c.Want {
			t.Errorf("%q:\n got  %q\n want %q", c.Name, got, c.Want)
		}
	}
}

// A prompt names only scopes the server would grant, and fewer: every scope
// it accepts passes ValidateScope.
func TestPromptScope_Fixtures(t *testing.T) {
	f := loadPromptFixture(t)
	s := loadScopeFixture(t)
	for _, scope := range append(f.AcceptedScopes, s.ValidScopes...) {
		if _, err := promptScope(scope); err != nil {
			t.Errorf("promptScope(%q): %v", scope, err)
		}
		if err := ValidateScope(scope); err != nil {
			t.Errorf("ValidateScope(%q): %v", scope, err)
		}
	}
	for _, scope := range append(f.RefusedScopes, s.InvalidScopes...) {
		if got, err := promptScope(scope); err == nil {
			t.Errorf("promptScope(%q) accepted: %q", scope, got)
		}
	}
}

// What the prompt can't word is refused, never shown as something less.
func TestGrantPrompt_RefusesWhatItCantWord(t *testing.T) {
	for _, c := range []struct{ scope, access string }{
		{"cie.*", "admin"},
		{"cie.*", "Write"},
		{"", "read"},
		{",", ""},
		{"cie.*\n", "read"},
	} {
		if got, err := GrantPrompt("suo archivio", c.scope, c.access, time.Minute); err == nil {
			t.Errorf("%q %q accepted: %q", c.scope, c.access, got)
		}
	}
}

// Durations are never understated, whatever the precision.
func TestPromptDuration_RoundsUp(t *testing.T) {
	for d, want := range map[time.Duration]string{
		500 * time.Millisecond: "1 secondo",
		59*time.Second + 1:     "1 minuto",
		61 * time.Second:       "2 minuti",
		10 * time.Minute:       "10 minuti",
		10*time.Minute + 1:     "11 minuti",
		time.Hour:              "60 minuti",
	} {
		if got := promptDuration(d); got != want {
			t.Errorf("%v: got %q, want %q", d, got, want)
		}
	}
}
