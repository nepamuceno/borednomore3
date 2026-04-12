package main

import (
	"context"
	"html/template"
	"io/fs"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	apiv1 "desar-server/internal/api/v1"
	"desar-server/internal/auth"
	"desar-server/internal/db"
	"desar-server/internal/notify"
	"desar-server/internal/scheduler"
	webhandlers "desar-server/internal/web"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

func main() {
	apiPort := envOr("API_PORT",   "8443")
	webPort  := envOr("WEB_PORT",  "8080")
	dbsPath  := envOr("DBS_PATH",  "./data")
	jwtKey   := envOr("JWT_SECRET","cambia-este-secreto-en-produccion-32chars")

	if err := db.Init(dbsPath); err != nil {
		log.Fatalf("BD init: %v", err)
	}
	auth.Init(jwtKey)

	notify.Init(notify.Config{
		SMTPHost:     envOr("SMTP_HOST", ""),
		SMTPPort:     envOr("SMTP_PORT", "587"),
		SMTPUser:     envOr("SMTP_USER", ""),
		SMTPPassword: envOr("SMTP_PASSWORD", ""),
		SMTPFrom:     envOr("SMTP_FROM", "noreply@desar.local"),
		Habilitado:   envOr("SMTP_HOST", "") != "",
	})

	scheduler.Init(db.Get())
	crearSuperadminSiNoExiste()

	tmpl, err := cargarTemplates()
	if err != nil {
		log.Fatalf("Templates: %v", err)
	}
	webhandlers.Init(tmpl)

	// ── API Router (puerto 8443) ──────────────────────────
	apiR := chi.NewRouter()
	apiR.Use(middleware.Recoverer, corsMiddleware)
	apiR.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			t := time.Now()
			next.ServeHTTP(w, r)
			log.Printf("API %s %s %s", r.Method, r.URL.Path, time.Since(t))
		})
	})
	// Mount API — rutas dentro del router son relativas a /desar/api/v1
	apiR.Mount("/desar/api/v1", apiv1.Router())

	// ── Web Router (puerto 8080) ──────────────────────────
	webR := chi.NewRouter()
	webR.Use(middleware.Recoverer, middleware.Compress(5))
	webR.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			t := time.Now()
			next.ServeHTTP(w, r)
			log.Printf("WEB %s %s %s", r.Method, r.URL.Path, time.Since(t))
		})
	})

	// Archivos estáticos
	webR.Handle("/desar/static/*",
		http.StripPrefix("/desar/static/",
			http.FileServer(http.Dir("./web/static"))))

	// Panel — el router interno usa rutas sin prefijo /desar
	// Usamos StripPrefix para que chi las resuelva correctamente
	webR.Mount("/desar", http.StripPrefix("/desar", webhandlers.Router()))

	// Redirect /desar → /desar/
	webR.Get("/desar", func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, "/desar/", http.StatusFound)
	})

	// ── Servidores ────────────────────────────────────────
	apiSrv := &http.Server{
		Addr:         ":" + apiPort,
		Handler:      apiR,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
	}
	webSrv := &http.Server{
		Addr:         ":" + webPort,
		Handler:      webR,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
	}

	go func() {
		log.Printf("🔌 API  :%s  → /desar/api/v1/ping", apiPort)
		if err := apiSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("API: %v", err)
		}
	}()
	go func() {
		log.Printf("🌐 Web  :%s  → http://localhost:%s/desar/", webPort, webPort)
		if err := webSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Web: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("Cerrando...")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	apiSrv.Shutdown(ctx)
	webSrv.Shutdown(ctx)
	log.Println("Servidor cerrado.")
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type,X-API-Key,Authorization")
		if r.Method == "OPTIONS" {
			w.WriteHeader(204)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func cargarTemplates() (*template.Template, error) {
	funcs := template.FuncMap{
		"formatTS": func(ts string) string {
			t, err := time.Parse(time.RFC3339, ts)
			if err != nil {
				t, err = time.Parse("2006-01-02T15:04:05", ts)
				if err != nil { return ts }
			}
			return t.Format("02/01/2006 15:04:05")
		},
		"formatDate": func(s string) string {
			if len(s) >= 10 { return s[:10] }
			return s
		},
		"now": time.Now,
	}
	tmpl := template.New("").Funcs(funcs)
	err := fs.WalkDir(os.DirFS("./web/templates"), ".", func(path string, d fs.DirEntry, _ error) error {
		if d.IsDir() || len(path) < 6 || path[len(path)-5:] != ".html" {
			return nil
		}
		content, e := os.ReadFile("./web/templates/" + path)
		if e != nil { return e }
		_, e = tmpl.New(path).Parse(string(content))
		return e
	})
	return tmpl, err
}

func envOr(k, def string) string {
	if v := os.Getenv(k); v != "" { return v }
	return def
}

func crearSuperadminSiNoExiste() {
	adminDB := db.Get().AdminDB()
	var n int
	adminDB.QueryRow("SELECT COUNT(*) FROM usuarios WHERE rol='superadmin'").Scan(&n)
	if n > 0 { return }

	apiKey := auth.GenerarAPIKey()
	dbPath := "./data/company_admin.db"
	res, err := adminDB.Exec(`INSERT INTO companias(nombre,api_key,plan,max_empleados,activo,db_path)
		VALUES('DESAR Admin',?,'enterprise',9999,1,?)`, apiKey, dbPath)
	if err != nil { return }
	compID, _ := res.LastInsertId()

	hash, _ := auth.HashPassword("admin123")
	adminDB.Exec(`INSERT INTO usuarios(compania_id,nombre,email,password_hash,rol)
		VALUES(?,'Super Admin','admin@desar.local',?,'superadmin')`, compID, hash)
	db.Get().CompanyDB(compID)

	log.Println("══════════════════════════════════════════════")
	log.Println("  SUPERADMIN: admin@desar.local / admin123")
	log.Printf("  Panel: http://localhost:%s/desar/", envOr("WEB_PORT","8080"))
	log.Println("  ⚠️  CAMBIA EL PASSWORD INMEDIATAMENTE")
	log.Println("══════════════════════════════════════════════")
}
