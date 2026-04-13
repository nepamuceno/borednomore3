package db

import (
	"regexp"
	"strings"
)

var rePlaceholder = regexp.MustCompile(`\$\d+`)
var reInsert = regexp.MustCompile(`(?i)^\s*INSERT\s+INTO`)

// Q convierte placeholders $N → ? para SQLite, sin cambios para PostgreSQL.
func Q(query string) string {
	if instance == nil || instance.mode == ModePostgres {
		return query
	}
	return rePlaceholder.ReplaceAllString(query, "?")
}

// QI es INSERT OR IGNORE (SQLite) / INSERT … ON CONFLICT DO NOTHING (PostgreSQL).
func QI(query string) string {
	if instance == nil || instance.mode == ModePostgres {
		q := rePlaceholder.ReplaceAllString(query, "$1") // no-op, ya correcto
		if !strings.Contains(strings.ToUpper(q), "ON CONFLICT") {
			q += " ON CONFLICT DO NOTHING"
		}
		return q
	}
	q := reInsert.ReplaceAllString(query, "INSERT OR IGNORE INTO")
	return rePlaceholder.ReplaceAllString(q, "?")
}
