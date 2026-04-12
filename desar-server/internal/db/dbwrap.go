package db

import "regexp"

var rePlaceholder = regexp.MustCompile(`\$\d+`)

// Q converts Postgres-style $N placeholders to SQLite ? when in SQLite mode.
func Q(query string) string {
	if instance == nil || instance.mode == ModePostgres {
		return query
	}
	return rePlaceholder.ReplaceAllString(query, "?")
}
