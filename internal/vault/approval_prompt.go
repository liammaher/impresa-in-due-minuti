package vault

import (
	"fmt"
	"path/filepath"
	"strings"
	"time"
	"unicode"
)

// The wording of an approval prompt (Touch ID, Windows Hello): what the user
// reads before a fingerprint or face lets a grant through. The Swift helper
// (cmd/pvault-touchid) words its Touch ID prompts the same way; both are held
// to testdata/prompts.json. A prompt is built only from a request the vault
// validated, or the vault's own summary of a signing request, and never
// understates what the grant allows.

const (
	// maxPromptPatterns and maxPromptPatternLength keep every pattern of a
	// scope visible in the prompt.
	maxPromptPatterns      = 10
	maxPromptPatternLength = 100
	maxShownNameLength     = 50
)

// promptScope splits a grant scope into the patterns a prompt names. It is
// stricter than ValidateScope, so a scope it accepts is granted as worded:
// at most maxPromptPatterns patterns of at most maxPromptPatternLength bytes,
// and only spaces and tabs are trimmed, so a line break never reaches it.
func promptScope(scope string) ([]string, error) {
	// Empty pieces stay, so "identity.*," is refused as ValidateScope refuses it.
	parts := strings.Split(scope, ",")
	if len(parts) > maxPromptPatterns {
		return nil, fmt.Errorf("scope must list 1 to %d patterns", maxPromptPatterns)
	}
	for i, p := range parts {
		p = strings.TrimFunc(p, func(r rune) bool { return r == '\t' || unicode.Is(unicode.Zs, r) })
		if _, ok := parseScopePattern(p); !ok || len(p) > maxPromptPatternLength {
			return nil, fmt.Errorf("invalid scope pattern %q", p)
		}
		parts[i] = p
	}
	return parts, nil
}

// PromptVaultLabel names the vault in prompts: "suo archivio", or "suo archivio
// «studio»" for a folder .pvault-studio (pvault --vault studio), so with several
// vaults an approval is never given for the wrong one. Prompts are in Italian:
// Impresa in un minuto's users are Italian, and a prompt completes the system's own sentence
// ("… sta tentando di …" on a Mac set to Italian), so it starts with a verb.
func PromptVaultLabel(dir string) string {
	if name, ok := strings.CutPrefix(filepath.Base(dir), ".pvault-"); ok && ValidPersonSlug(name) {
		return "suo archivio «" + name + "»"
	}
	return "suo archivio"
}

// GrantPrompt completes "Impresa in un minuto chiede di …" for a grant of scope with access
// (read if empty), lasting ttl; an empty scope (and access) is full access.
// A scope or access it can't word is an error, never a vaguer prompt.
func GrantPrompt(label, scope, access string, ttl time.Duration) (string, error) {
	if scope == "" {
		if access != "" {
			return "", fmt.Errorf("access needs a scope")
		}
		return fmt.Sprintf("avere accesso completo al %s, impostazioni e chiavi degli agenti comprese, per %s", label, promptDuration(ttl)), nil
	}
	patterns, err := promptScope(scope)
	if err != nil {
		return "", err
	}
	// Every scoped grant can read what it covers, append and write included.
	var verb string
	switch access {
	case "", AccessRead:
		verb = "leggere dal " + label
	case AccessAppend:
		verb = "leggere e completare, senza cambiare ciò che c'è, nel " + label
	case AccessWrite:
		verb = "leggere, modificare ed eliminare nel " + label
	default:
		return "", fmt.Errorf("access must be read, append or write")
	}
	// "*" covers everything, so it is named alone rather than last in a list.
	var what string
	for _, p := range patterns {
		if p == "*" {
			what = describePattern(label, "*")
		}
	}
	if what == "" {
		names, documents := make([]string, len(patterns)), false
		for i, p := range patterns {
			names[i] = describePattern(label, p)
			documents = documents || strings.HasSuffix(p, ".*") && !strings.HasSuffix(p, ":*")
		}
		what = strings.Join(names, ", ")
		// A category pattern also covers <category>.documents (ScopeAllows).
		if documents {
			what += " (documenti compresi)"
		}
	}
	return fmt.Sprintf("%s, per %s: %s", verb, promptDuration(ttl), what), nil
}

// SignPrompt completes "Impresa in un minuto chiede di …" for reviewing a signing request,
// from the vault's own summary of it. The grant it unlocks reads the signed
// file and approves it, so the wording says sign, not read.
func SignPrompt(label, name string, pages int, hash8, requester string, ttl time.Duration) string {
	count := fmt.Sprintf("%d pagine", pages)
	if pages == 1 {
		count = "1 pagina"
	}
	return fmt.Sprintf(`rivedere e firmare «%s» (%s, codice %s), inviato da %s, con la sua firma autografa dal %s, per %s`,
		shownName(name), count, hash8, shownName(requester), label, promptDuration(ttl))
}

// shownName keeps what an agent chose as a name harmless in a prompt:
// letters, marks, digits, spaces and . _ - ( ); anything else (quotes, bidi
// controls, line breaks) shows as ?, and a long name is cut. Length counts
// runes, not characters: a character can stack any number of accents, which
// would push the rest of the prompt out of sight.
func shownName(name string) string {
	var out []rune
	for _, r := range name {
		if unicode.IsLetter(r) || unicode.IsMark(r) || unicode.IsNumber(r) || strings.ContainsRune(" ._-()", r) {
			out = append(out, r)
		} else {
			out = append(out, '?')
		}
	}
	for len(out) > 0 && out[0] == ' ' {
		out = out[1:]
	}
	for len(out) > 0 && out[len(out)-1] == ' ' {
		out = out[:len(out)-1]
	}
	if len(out) > maxShownNameLength {
		out = append(out[:maxShownNameLength-1], '…')
	}
	if len(out) == 0 {
		return "?"
	}
	return string(out)
}

// PromptCategories names each schema category in prompts; another (a numbered
// copy, cie2) shows as it is. The Touch ID helper has the same list, and both
// are held to testdata/prompts.json.
var PromptCategories = map[string]string{
	"identity": "anagrafica", "cie": "carta d'identità", "spid": "SPID", "residenza": "residenza",
	"domicilio": "domicilio", "abitazione": "abitazione", "locazione": "contratto d'affitto",
	"utenze": "utenze", "tari": "TARI", "pratiche": "pratiche", "famiglia": "famiglia", "ruolo": "ruolo",
	"procura": "procura", "business": "impresa", "locale": "locale", "immobile": "immobile",
	"albo": "albo professionale", "cassa": "cassa previdenziale", "firma_digitale": "firma digitale",
	"firma_autografa": "firma autografa", "permesso_soggiorno": "permesso di soggiorno",
	"passaporto": "passaporto", "tessera_sanitaria": "tessera sanitaria", "patente": "patente",
	"addresses": "altri indirizzi", "financial": "dati fiscali e finanziari", "payment": "carta di pagamento",
	"preferences": "preferenze", "employment": "lavoro", "medical": "dati medici", "documents": "documenti",
	"files": "file",
}

func promptCategory(c string) string {
	if l, ok := PromptCategories[c]; ok {
		return l
	}
	return c
}

func describePattern(label, pattern string) string {
	if pattern == "*" {
		if label == "suo archivio" {
			return "tutto, compresi i dati dei suoi familiari"
		}
		return "tutto, compresi i dati di ogni persona che contiene"
	}
	// Whose data: the owner's (no prefix), one person's, or everyone's.
	mine, of, rest := true, "", pattern
	if person, local, ok := strings.Cut(pattern, ":"); ok {
		rest = local
		if rest == "*" {
			return "tutto ciò che riguarda " + person
		}
		mine, of = false, " di "+person
		if person == "*" {
			of = " di tutte le persone"
		}
	}
	if category, ok := strings.CutSuffix(rest, ".*"); ok {
		if mine {
			return "i suoi dati di " + promptCategory(category)
		}
		return "i dati di " + promptCategory(category) + of
	}
	if category, ok := strings.CutSuffix(rest, ".documents"); ok {
		if mine {
			return "i suoi documenti di " + promptCategory(category)
		}
		return "i documenti di " + promptCategory(category) + of
	}
	return "il campo " + rest + of
}

func promptDuration(d time.Duration) string {
	s := int((d + time.Second - 1) / time.Second)
	switch {
	case s == 1:
		return "1 secondo"
	case s < 60:
		return fmt.Sprintf("%d secondi", s)
	}
	m := (s + 59) / 60 // round up: never understate how long a grant lasts
	if m == 1 {
		return "1 minuto"
	}
	return fmt.Sprintf("%d minuti", m)
}
