package auth

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"desar-server/internal/models"

	jwt "github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

var jwtSecret []byte

func Init(secret string) { jwtSecret = []byte(secret) }

type ctxKey string

const ClaimsKey ctxKey = "claims"

// ── Roles disponibles en el sistema ──────────────────────────
// Orden importa: de mayor a menor privilegio
var Roles = []string{"superadmin", "admin", "gerente", "rrhh", "supervisor", "readonly"}

// RolesDisponibles retorna los roles que un usuario puede asignar
// según su propio rol (un rol solo puede crear/editar roles menores)
func RolesDisponibles(rolActor string) []string {
	idx := -1
	for i, r := range Roles {
		if r == rolActor {
			idx = i
			break
		}
	}
	if idx == -1 {
		return nil
	}
	// superadmin puede asignar todos los roles excepto superadmin
	// admin puede asignar desde admin hacia abajo
	start := idx
	if rolActor == "superadmin" {
		start = 0 // puede asignar todos incluyendo admin (pero no otros superadmin por seguridad)
	}
	return Roles[start:]
}

// ── Permisos por rol ──────────────────────────────────────────
// Formato: "recurso.accion" — soporta wildcard "recurso.*" y "*"
// Acciones: ver | crear | editar | eliminar (incluidos en ".*")
var permisos = map[string][]string{
	"superadmin": {"*"},
	"admin":      {"companias.ver", "empleados.*", "registros.*", "sitios.*", "reportes.*", "usuarios.*", "config.*", "pdf.*"},
	"gerente":    {"empleados.ver", "empleados.editar", "registros.*", "sitios.ver", "sitios.editar", "reportes.*", "pdf.*"},
	"rrhh":       {"empleados.*", "sitios.*", "registros.ver", "registros.crear", "reportes.ver", "pdf.ver"},
	"supervisor": {"registros.ver", "registros.crear", "empleados.ver"},
	"readonly":   {"empleados.ver", "registros.ver"},
}

func Puede(rol, permiso string) bool {
	p, ok := permisos[rol]
	if !ok {
		return false
	}
	for _, v := range p {
		if v == "*" || v == permiso {
			return true
		}
		parts := strings.SplitN(v, ".", 2)
		if len(parts) == 2 && parts[1] == "*" {
			pparts := strings.SplitN(permiso, ".", 2)
			if len(pparts) == 2 && pparts[0] == parts[0] {
				return true
			}
		}
	}
	return false
}

func RequierePermiso(permiso string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			claims := r.Context().Value(ClaimsKey).(*models.Claims)
			if !Puede(claims.Rol, permiso) {
				http.Error(w, "403 sin permisos", http.StatusForbidden)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

// ── JWT ───────────────────────────────────────────────────────
func GenerarToken(u *models.Usuario) (string, error) {
	claims := jwt.MapClaims{
		"user_id":     u.ID,
		"compania_id": u.CompaniaID,
		"rol":         u.Rol,
		"email":       u.Email,
		"exp":         time.Now().Add(8 * time.Hour).Unix(),
	}
	return jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString(jwtSecret)
}

func ParsearToken(tokenStr string) (*models.Claims, error) {
	t, err := jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
		if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("método inválido")
		}
		return jwtSecret, nil
	})
	if err != nil || !t.Valid {
		return nil, fmt.Errorf("token inválido")
	}
	mc := t.Claims.(jwt.MapClaims)
	return &models.Claims{
		UserID:     int64(mc["user_id"].(float64)),
		CompaniaID: int64(mc["compania_id"].(float64)),
		Rol:        mc["rol"].(string),
		Email:      mc["email"].(string),
	}, nil
}

// ── Middleware JWT panel web (cookie) ─────────────────────────
func MiddlewareWeb(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		cookie, err := r.Cookie("desar_token")
		if err != nil {
			http.Redirect(w, r, "/desar/login", http.StatusFound)
			return
		}
		claims, err := ParsearToken(cookie.Value)
		if err != nil {
			http.Redirect(w, r, "/desar/login", http.StatusFound)
			return
		}
		ctx := context.WithValue(r.Context(), ClaimsKey, claims)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// ── Middleware API Key APK ────────────────────────────────────
const APIKeyHeader = "X-API-Key"

func GetAPIKey(r *http.Request) string { return r.Header.Get(APIKeyHeader) }

// ── Middleware JWT API REST ───────────────────────────────────
func MiddlewareAPI(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		a := r.Header.Get("Authorization")
		if !strings.HasPrefix(a, "Bearer ") {
			http.Error(w, `{"ok":false,"mensaje":"sin token"}`, http.StatusUnauthorized)
			return
		}
		claims, err := ParsearToken(strings.TrimPrefix(a, "Bearer "))
		if err != nil {
			http.Error(w, `{"ok":false,"mensaje":"token inválido"}`, http.StatusUnauthorized)
			return
		}
		ctx := context.WithValue(r.Context(), ClaimsKey, claims)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// ── Password ──────────────────────────────────────────────────
func HashPassword(pw string) (string, error) {
	b, err := bcrypt.GenerateFromPassword([]byte(pw), 12)
	return string(b), err
}

func VerificarPassword(hash, pw string) bool {
	return bcrypt.CompareHashAndPassword([]byte(hash), []byte(pw)) == nil
}

// ── API Key generator ─────────────────────────────────────────
func GenerarAPIKey() string {
	b := make([]byte, 24)
	rand.Read(b)
	return "desar_" + hex.EncodeToString(b)
}

// ── Context helpers ───────────────────────────────────────────
func ClaimsFromCtx(r *http.Request) *models.Claims {
	c, _ := r.Context().Value(ClaimsKey).(*models.Claims)
	return c
}

func esHTTPS(r *http.Request) bool {
	if r != nil && r.TLS != nil {
		return true
	}
	if r != nil && r.Header.Get("X-Forwarded-Proto") == "https" {
		return true
	}
	return os.Getenv("FORCE_HTTPS") == "1"
}

func SetCookie(w http.ResponseWriter, token string, r ...*http.Request) {
	secure := false
	if len(r) > 0 {
		secure = esHTTPS(r[0])
	}
	http.SetCookie(w, &http.Cookie{
		Name:     "desar_token",
		Value:    token,
		Path:     "/desar",
		HttpOnly: true,
		Secure:   secure,
		SameSite: http.SameSiteLaxMode,
		MaxAge:   8 * 3600,
	})
}

func ClearCookie(w http.ResponseWriter) {
	http.SetCookie(w, &http.Cookie{
		Name:   "desar_token",
		Value:  "",
		Path:   "/desar",
		MaxAge: -1,
	})
}
