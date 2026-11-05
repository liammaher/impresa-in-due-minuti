package vault

import (
	"encoding/json"
	"os"
	"testing"
)

// TestSharedValueCases holds NormalizeAndValidate to testdata/values.json, which
// plugin/test_check.py holds the plugin's check.py to: the plugin has no vault and
// copies these rules, so the one file keeps the two from drifting apart.
func TestSharedValueCases(t *testing.T) {
	raw, err := os.ReadFile("testdata/values.json")
	if err != nil {
		t.Fatal(err)
	}
	var doc struct {
		Cases []struct {
			ID    string  `json:"id"`
			Value string  `json:"value"`
			Want  *string `json:"want"`
		} `json:"cases"`
	}
	if err := json.Unmarshal(raw, &doc); err != nil {
		t.Fatal(err)
	}
	if len(doc.Cases) == 0 {
		t.Fatal("no cases")
	}
	for _, c := range doc.Cases {
		got, err := NormalizeAndValidate(c.ID, c.Value)
		switch {
		case c.Want == nil && err == nil:
			t.Errorf("%s %q: accepted as %q, want refused", c.ID, c.Value, got)
		case c.Want != nil && err != nil:
			t.Errorf("%s %q: refused (%v), want %q", c.ID, c.Value, err, *c.Want)
		case c.Want != nil && got != *c.Want:
			t.Errorf("%s %q: got %q, want %q", c.ID, c.Value, got, *c.Want)
		}
	}
}
