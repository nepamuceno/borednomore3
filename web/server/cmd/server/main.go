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
	webhandlers "desar-server/internal/web"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

func main() {
	apiPort := envOr("API_PORT", "8443")
	webPort := envOr("WEB_PORT", "8080")
	dbsPath := envOr("DBS_PATH", "./data")
	jwtKey  := envOr("JWT_SECRET", "cambia-este-secreto-en-produccion-32chars")

	if err := db.Init(dbsPath); err != nil {
		log.Fatalf("BD init: %v", err)
	}
	auth.Init(jwtKey)
	crearSuperadminSiNoExiste()

	// Cargar templates desde disco (desarrollo) o embed (producción)
	tmpl, err := cargarTemplates()
	if err != nil {
		log.Fatalf("Templates: %v", err)
	}
	webhandlers.Init(tmpl)

	// Router API
	apiRouter := chi.NewRouter()
	apiRouter.Use(middleware.Logger, middleware.Recoverer, corsMiddleware)
	apiRouter.Mount("/desar/api/v1", apiv1.Router())

	// Router Web
	webRouter := chi.NewRouter()
	webRouter.Use(middleware.Logger, middleware.Recoverer, middleware.Compress(5))

	// Servir estáticos desde ./web/static/
	staticDir := http.Dir("./web/static")
	webRouter.Handle("/desar/static/*",
		http.StripPrefix("/desar/static/", http.FileServer(staticDir)))

	webRouter.Mount("/desar", webhandlers.Router())
	webRouter.Get("/desar", func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, "/desar/", http.StatusFound)
	})

	apiSrv := &http.Server{Addr: ":" + apiPort, Handler: apiRouter,
		ReadTimeout: 15 * time.Second, WriteTimeout: 15 * time.Second}
	webSrv := &http.Server{Addr: ":" + webPort, Handler: webRouter,
		ReadTimeout: 15 * time.Second, WriteTimeout: 15 * time.Second}

	go func() {
		log.Printf("🔌 API  ::%s  → /desar/api/v1/", apiPort)
		if err := apiSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("API: %v", err)
		}
	}()
	go func() {
		log.Printf("🌐 Web  ::%s  → /desar/", webPort)
		if err := webSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Web: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	apiSrv.Shutdown(ctx)
	webSrv.Shutdown(ctx)
	log.Println("Servidor cerrado.")
}

func cargarTemplates() (*template.Template, error) {
	funcs := template.FuncMap{
		"formatTS": func(ts string) string {
			t, err := time.Parse(time.RFC3339, ts)
			if err != nil { return ts }
			return t.Format("02/01/2006 15:04:05")
		},
		"formatDate": func(s string) string {
			if len(s) >= 10 { return s[:10] }
			return s
		},
		"now": func() time.Time { return time.Now() },
	}

	tmpl := template.New("").Funcs(funcs)

	// Cargar todos los .html recursivamente desde ./web/templates/
	err := fs.WalkDir(os.DirFS("./web/templates"), ".", func(path string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() || !isHTML(path) { return err }
		content, e := os.ReadFile("./web/templates/" + path)
		if e != nil { return e }
		_, e = tmpl.New(path).Parse(string(content))
		return e
	})
	return tmpl, err
}

func isHTML(path string) bool {
	return len(path) > 5 && path[len(path)-5:] == ".html"
}

func envOr(k, def string) string {
	if v := os.Getenv(k); v != "" { return v }
	return def
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type,X-API-Key,Authorization")
		if r.Method == "OPTIONS" { w.WriteHeader(204); return }
		next.ServeHTTP(w, r)
	})
}

func crearSuperadminSiNoExiste() {
	adminDB := db.Get().AdminDB()
	var count int
	adminDB.QueryRow("SELECT COUNT(*) FROM usuarios WHERE rol='superadmin'").Scan(&count)
	if count > 0 { return }

	apiKey := auth.GenerarAPIKey()
	dbPath := "./data/company_admin.db"
	res, err := adminDB.Exec(`INSERT INTO companias(nombre,api_key,plan,max_empleados,activo,db_path)
		VALUES('DESAR Admin',?,  'enterprise',9999,1,?)`, apiKey, dbPath)
	if err != nil { log.Printf("Compañía admin: %v", err); return }
	compID, _ := res.LastInsertId()

	hash, _ := auth.HashPassword("admin123")
	adminDB.Exec(`INSERT INTO usuarios(compania_id,nombre,email,password_hash,rol)
		VALUES(?,'Super Admin','admin@desar.local',?,'superadmin')`, compID, hash)

	db.Get().CompanyDB(compID) // inicializa la BD

	log.Printf("══════════════════════════════════════════")
	log.Printf("  SUPERADMIN: admin@desar.local / admin123")
	log.Printf("  Panel:      http://localhost:%s/desar/", envOr("WEB_PORT","8080"))
	log.Printf("  ⚠️  CAMBIA EL PASSWORD INMEDIATAMENTE")
	log.Printf("══════════════════════════════════════════")
}
