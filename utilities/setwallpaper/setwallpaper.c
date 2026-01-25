// /home/deb/borednomore3/borednomore3/setwallpaper/setwallpaper.c
#include <X11/Xlib.h>
#include <X11/Xatom.h>
#include <Imlib2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/time.h>
#include <signal.h>
#include <errno.h>

// Desktop environment detection
typedef enum {
    DE_UNKNOWN = 0,
    DE_LXQT,
    DE_LXDE,
    DE_GNOME,
    DE_KDE,
    DE_XFCE,
    DE_MATE,
    DE_CINNAMON,
    DE_UNITY,
    DE_WAYLAND_GENERIC
} DesktopEnvironment;

// Session type detection
typedef enum {
    SESSION_X11 = 0,
    SESSION_WAYLAND,
    SESSION_UNKNOWN
} SessionType;

// Configuration constants
#define DESKTOP_SYNC_DELAY_MS 100      // Base delay for desktop synchronization
#define MAX_DESKTOP_WAIT_MS 2000       // Maximum time to wait for desktop
#define X11_SYNC_TIMEOUT_MS 500        // X11 sync timeout
#define WAYLAND_SYNC_DELAY_MS 200      // Wayland-specific delay
#define BLANK_PAGE_FIX_DELAY_MS 250    // Specific delay to prevent blank pages

// Function prototypes
DesktopEnvironment detect_desktop_environment();
SessionType detect_session_type();
int set_wallpaper_x11_simple(const char *filename);  // Your original method
int set_wallpaper_x11_enhanced(const char *filename); // Enhanced with sync
int set_wallpaper_wayland(const char *filename);
int set_wallpaper_gnome(const char *filename);
int set_wallpaper_kde(const char *filename);
int set_wallpaper_universal(const char *filename);
void print_usage(const char *program_name);
int wait_for_desktop_ready(DesktopEnvironment de, SessionType session);
int sync_with_pcmanfm_qt(void);
int sync_with_wayland_compositor(void);
unsigned long get_time_ms(void);
int check_x11_sync(Display *dpy);
int ensure_pcmanfm_qt_ready(void);
int detect_blank_page_issue(void);

// Get current time in milliseconds
unsigned long get_time_ms(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (tv.tv_sec * 1000) + (tv.tv_usec / 1000);
}

// Your original simple X11 method - preserved exactly as is
int set_wallpaper_x11_simple(const char *filename) {
    Display *dpy = XOpenDisplay(NULL);
    if (!dpy) {
        fprintf(stderr, "No se pudo abrir el display X11\n");
        return 1;
    }

    Window root = DefaultRootWindow(dpy);
    Imlib_Image img = imlib_load_image(filename);
    if (!img) {
        fprintf(stderr, "No se pudo cargar la imagen: %s\n", filename);
        XCloseDisplay(dpy);
        return 1;
    }

    imlib_context_set_display(dpy);
    imlib_context_set_visual(DefaultVisual(dpy, DefaultScreen(dpy)));
    imlib_context_set_colormap(DefaultColormap(dpy, DefaultScreen(dpy)));
    imlib_context_set_drawable(root);
    imlib_context_set_image(img);

    int screen = DefaultScreen(dpy);
    int width = DisplayWidth(dpy, screen);
    int height = DisplayHeight(dpy, screen);

    Imlib_Image scaled = imlib_create_cropped_scaled_image(
        0, 0,
        imlib_image_get_width(), imlib_image_get_height(),
        width, height
    );
    imlib_free_image();
    imlib_context_set_image(scaled);

    Pixmap pix = XCreatePixmap(dpy, root, width, height,
                               DefaultDepth(dpy, screen));
    imlib_context_set_drawable(pix);
    imlib_render_image_on_drawable(0, 0);

    Atom prop = XInternAtom(dpy, "_XROOTPMAP_ID", False);
    XChangeProperty(dpy, root, prop, XA_PIXMAP, 32, PropModeReplace,
                    (unsigned char *)&pix, 1);

    XSetWindowBackgroundPixmap(dpy, root, pix);
    XClearWindow(dpy, root);
    XFlush(dpy);

    imlib_free_image();
    XCloseDisplay(dpy);

    return 0;
}

// Enhanced X11 method with synchronization (for fallback use)
int set_wallpaper_x11_enhanced(const char *filename) {
    Display *dpy = XOpenDisplay(NULL);
    if (!dpy) {
        fprintf(stderr, "No se pudo abrir el display X11\n");
        return 1;
    }

    Window root = DefaultRootWindow(dpy);
    Imlib_Image img = imlib_load_image(filename);
    if (!img) {
        fprintf(stderr, "No se pudo cargar la imagen: %s\n", filename);
        XCloseDisplay(dpy);
        return 1;
    }

    imlib_context_set_display(dpy);
    imlib_context_set_visual(DefaultVisual(dpy, DefaultScreen(dpy)));
    imlib_context_set_colormap(DefaultColormap(dpy, DefaultScreen(dpy)));
    imlib_context_set_drawable(root);
    imlib_context_set_image(img);

    int screen = DefaultScreen(dpy);
    int width = DisplayWidth(dpy, screen);
    int height = DisplayHeight(dpy, screen);

    Imlib_Image scaled = imlib_create_cropped_scaled_image(
        0, 0,
        imlib_image_get_width(), imlib_image_get_height(),
        width, height
    );
    imlib_free_image();
    imlib_context_set_image(scaled);

    Pixmap pix = XCreatePixmap(dpy, root, width, height,
                               DefaultDepth(dpy, screen));
    imlib_context_set_drawable(pix);
    imlib_render_image_on_drawable(0, 0);

    // Synchronize X11 before setting properties
    XSync(dpy, False);
    while (XPending(dpy)) {
        XEvent event;
        XNextEvent(dpy, &event);
    }

    Atom prop = XInternAtom(dpy, "_XROOTPMAP_ID", False);
    XChangeProperty(dpy, root, prop, XA_PIXMAP, 32, PropModeReplace,
                    (unsigned char *)&pix, 1);

    XSetWindowBackgroundPixmap(dpy, root, pix);
    XClearWindow(dpy, root);
    
    // Force X11 to process all commands immediately
    XSync(dpy, False);
    XFlush(dpy);

    imlib_free_image();
    XCloseDisplay(dpy);

    return 0;
}

// Detect blank page issues
int detect_blank_page_issue(void) {
    // Check for rapid wallpaper changes that might cause blank pages
    static unsigned long last_call_time = 0;
    unsigned long current_time = get_time_ms();
    
    if (last_call_time > 0) {
        unsigned long elapsed = current_time - last_call_time;
        if (elapsed < 100) { // Less than 100ms between calls
            return 1; // Likely to cause blank pages
        }
    }
    
    last_call_time = current_time;
    return 0;
}

// Detect session type (X11 or Wayland)
SessionType detect_session_type() {
    const char *wayland_display = getenv("WAYLAND_DISPLAY");
    const char *x11_display = getenv("DISPLAY");
    const char *session_type = getenv("XDG_SESSION_TYPE");
    
    // Check explicit session type first
    if (session_type) {
        if (strstr(session_type, "wayland"))
            return SESSION_WAYLAND;
        if (strstr(session_type, "x11"))
            return SESSION_X11;
    }
    
    // Check environment variables
    if (wayland_display && strlen(wayland_display) > 0)
        return SESSION_WAYLAND;
    
    if (x11_display && strlen(x11_display) > 0)
        return SESSION_X11;
    
    return SESSION_UNKNOWN;
}

// Desktop environment detection
DesktopEnvironment detect_desktop_environment() {
    const char *desktop_session = getenv("DESKTOP_SESSION");
    const char *xdg_current_desktop = getenv("XDG_CURRENT_DESKTOP");
    const char *wayland_session = getenv("WAYLAND_DISPLAY");
    
    // Special handling for Wayland sessions
    if (wayland_session && strlen(wayland_session) > 0) {
        if (xdg_current_desktop) {
            if (strstr(xdg_current_desktop, "GNOME"))
                return DE_GNOME;
            if (strstr(xdg_current_desktop, "KDE"))
                return DE_KDE;
        }
        return DE_WAYLAND_GENERIC;
    }
    
    if (desktop_session) {
        if (strstr(desktop_session, "lxqt") || strstr(desktop_session, "LXQt"))
            return DE_LXQT;
        if (strstr(desktop_session, "lxde") || strstr(desktop_session, "LXDE"))
            return DE_LXDE;
        if (strstr(desktop_session, "gnome") || strstr(desktop_session, "GNOME"))
            return DE_GNOME;
        if (strstr(desktop_session, "kde") || strstr(desktop_session, "KDE") || 
            strstr(desktop_session, "plasma") || strstr(desktop_session, "PLASMA"))
            return DE_KDE;
        if (strstr(desktop_session, "xfce") || strstr(desktop_session, "XFCE"))
            return DE_XFCE;
        if (strstr(desktop_session, "mate") || strstr(desktop_session, "MATE"))
            return DE_MATE;
        if (strstr(desktop_session, "cinnamon") || strstr(desktop_session, "CINNAMON"))
            return DE_CINNAMON;
        if (strstr(desktop_session, "unity") || strstr(desktop_session, "Unity"))
            return DE_UNITY;
    }
    
    if (xdg_current_desktop) {
        if (strstr(xdg_current_desktop, "LXQt"))
            return DE_LXQT;
        if (strstr(xdg_current_desktop, "GNOME"))
            return DE_GNOME;
        if (strstr(xdg_current_desktop, "KDE"))
            return DE_KDE;
    }
    
    return DE_UNKNOWN;
}

// GNOME wallpaper setter using gsettings
int set_wallpaper_gnome(const char *filename) {
    char command[1024];
    snprintf(command, sizeof(command), "gsettings set org.gnome.desktop.background picture-uri 'file://%s'", filename);
    return system(command);
}

// KDE wallpaper setter using qdbus
int set_wallpaper_kde(const char *filename) {
    char command[1024];
    snprintf(command, sizeof(command), 
        "qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript '"
        "var allDesktops = desktops(); "
        "for (i=0;i<allDesktops.length;i++) { "
        "d = allDesktops[i]; d.wallpaperPlugin = \"org.kde.image\"; "
        "d.currentConfigGroup = Array(\"Wallpaper\", \"org.kde.image\", \"General\"); "
        "d.writeConfig(\"Image\", \"file://%s\")"
        "}'", filename);
    return system(command);
}

// Wayland wallpaper setter (uses external tools)
int set_wallpaper_wayland(const char *filename) {
    fprintf(stderr, "Info: Using Wayland wallpaper setting method\n");
    
    // Try different Wayland wallpaper tools
    const char *wayland_commands[] = {
        "swaybg -i '%s' -m fill",
        "waywall -s '%s'",
        "himmel '%s'",
        "oguri '%s'",
        NULL
    };
    
    for (int i = 0; wayland_commands[i] != NULL; i++) {
        char command[1024];
        snprintf(command, sizeof(command), wayland_commands[i], filename);
        
        // Check if command exists
        char check_cmd[1024];
        char *cmd_copy = strdup(wayland_commands[i]);
        char *cmd_name = strtok(cmd_copy, " ");
        snprintf(check_cmd, sizeof(check_cmd), "which %s > /dev/null 2>&1", cmd_name);
        free(cmd_copy);
        
        if (system(check_cmd) == 0) {
            fprintf(stderr, "Using Wayland tool: %s\n", strtok(strdup(wayland_commands[i]), " "));
            return system(command);
        }
    }
    
    // Fallback: try to use desktop-specific methods
    DesktopEnvironment de = detect_desktop_environment();
    if (de == DE_GNOME) {
        return set_wallpaper_gnome(filename);
    } else if (de == DE_KDE) {
        return set_wallpaper_kde(filename);
    }
    
    fprintf(stderr, "Error: No Wayland wallpaper tool found\n");
    fprintf(stderr, "Please install one of: swaybg, waywall, himmel, oguri\n");
    return 1;
}

// Smart synchronization for LXQt/LXDE without manual pcmanfm-qt restart
int sync_with_pcmanfm_qt(void) {
    // Check if pcmanfm-qt is running
    FILE *fp = popen("pgrep -x pcmanfm-qt", "r");
    if (!fp) return -1;
    
    char line[32];
    int pcmanfm_running = (fgets(line, sizeof(line), fp) != NULL);
    pclose(fp);
    
    if (!pcmanfm_running) {
        // Try to start pcmanfm-qt in desktop mode automatically
        fprintf(stderr, "Info: Starting pcmanfm-qt desktop mode...\n");
        int result = system("pcmanfm-qt --desktop &");
        if (result == 0) {
            sleep(1); // Wait for initialization
            return 0;
        } else {
            fprintf(stderr, "Warning: Could not start pcmanfm-qt\n");
            return -1;
        }
    }
    
    // Give pcmanfm-qt time to process the previous change
    usleep(BLANK_PAGE_FIX_DELAY_MS * 1000); // 250ms to prevent blank pages
    
    return 0;
}

// Smart universal setter that uses your method first, then falls back
int set_wallpaper_smart(const char *filename) {
    DesktopEnvironment de = detect_desktop_environment();
    SessionType session = detect_session_type();
    
    // Handle Wayland sessions
    if (session == SESSION_WAYLAND) {
        return set_wallpaper_wayland(filename);
    }
    
    // For rapid wallpaper changes, detect potential blank page issues
    if (detect_blank_page_issue()) {
        fprintf(stderr, "Info: Detected rapid wallpaper changes, applying synchronization\n");
        if (sync_with_pcmanfm_qt() != 0) {
            usleep(BLANK_PAGE_FIX_DELAY_MS * 1000);
        }
    }
    
    // Try your original simple method first (default execution)
    int result = set_wallpaper_x11_simple(filename);
    
    // If simple method fails or we're in a problematic environment, use enhanced version
    if (result != 0 || (de == DE_LXQT || de == DE_LXDE)) {
        fprintf(stderr, "Info: Using enhanced method for better compatibility\n");
        
        // Wait for desktop to be ready
        if (wait_for_desktop_ready(de, session) != 0) {
            fprintf(stderr, "Warning: Desktop sync failed, proceeding anyway\n");
        }
        
        // Use enhanced method
        result = set_wallpaper_x11_enhanced(filename);
        
        // Additional sync for LXQt/LXDE
        if (result == 0 && (de == DE_LXQT || de == DE_LXDE)) {
            sync_with_pcmanfm_qt();
        }
    }
    
    return result;
}

// Wait for desktop environment to be ready
int wait_for_desktop_ready(DesktopEnvironment de, SessionType session) {
    unsigned long start_time = get_time_ms();
    int max_wait_ms = MAX_DESKTOP_WAIT_MS;
    
    // Session-specific handling
    if (session == SESSION_WAYLAND) {
        return 0; // Wayland handled separately
    }
    
    switch (de) {
        case DE_LXQT:
        case DE_LXDE:
            // Special handling for LXQt/LXDE with pcmanfm-qt
            if (sync_with_pcmanfm_qt() != 0) {
                // Fallback: standard delay with extra time for LXQt
                usleep(BLANK_PAGE_FIX_DELAY_MS * 1000);
            }
            break;
            
        case DE_GNOME:
        case DE_KDE:
        case DE_XFCE:
        case DE_MATE:
        case DE_CINNAMON:
        case DE_UNITY:
            // Standard delay for other environments
            usleep(DESKTOP_SYNC_DELAY_MS * 1000);
            break;
            
        default:
            // Minimal delay for unknown environments
            usleep(DESKTOP_SYNC_DELAY_MS * 500);
            break;
    }
    
    // Ensure we don't exceed maximum wait time
    unsigned long elapsed = get_time_ms() - start_time;
    if (elapsed > max_wait_ms) {
        fprintf(stderr, "Warning: Desktop sync timeout after %lu ms\n", elapsed);
        return -1;
    }
    
    return 0;
}

void print_usage(const char *program_name) {
    printf("Uso: %s <imagen>\n", program_name);
    printf("Cambia el fondo de pantalla usando el método más apropiado para el entorno de escritorio detectado.\n");
    printf("\nEntornos soportados:\n");
    printf("  - LXQt/LXDE (método X11 nativo con sincronización inteligente)\n");
    printf("  - GNOME (gsettings)\n");
    printf("  - KDE Plasma (qdbus)\n");
    printf("  - XFCE, MATE, Cinnamon, Unity (método X11 nativo)\n");
    printf("  - Wayland (swaybg, waywall, himmel, oguri)\n");
    printf("  - Otros (método X11 nativo como respaldo)\n");
    printf("\nEste programa usa tu método X11 original por defecto y aplica sincronización solo cuando es necesario.\n");
    printf("No es necesario reiniciar pcmanfm-qt manualmente.\n");
}

// Main function - uses smart method that preserves your original approach
int main(int argc, char **argv) {
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    const char *filename = argv[1];
    
    // Check if file exists
    if (access(filename, F_OK) != 0) {
        fprintf(stderr, "Error: El archivo '%s' no existe\n", filename);
        return 1;
    }

    DesktopEnvironment de = detect_desktop_environment();
    SessionType session = detect_session_type();
    const char *de_name = "Desconocido";
    const char *session_type = "Unknown";
    
    switch (de) {
        case DE_LXQT: de_name = "LXQt"; break;
        case DE_LXDE: de_name = "LXDE"; break;
        case DE_GNOME: de_name = "GNOME"; break;
        case DE_KDE: de_name = "KDE Plasma"; break;
        case DE_XFCE: de_name = "XFCE"; break;
        case DE_MATE: de_name = "MATE"; break;
        case DE_CINNAMON: de_name = "Cinnamon"; break;
        case DE_UNITY: de_name = "Unity"; break;
        case DE_WAYLAND_GENERIC: de_name = "Wayland"; break;
        default: break;
    }
    
    switch (session) {
        case SESSION_X11: session_type = "X11"; break;
        case SESSION_WAYLAND: session_type = "Wayland"; break;
        default: session_type = "Unknown"; break;
    }
    
    printf("Entorno de escritorio detectado: %s (%s)\n", de_name, session_type);
    
    int result = set_wallpaper_smart(filename);
    
    if (result == 0) {
        printf("Fondo de pantalla cambiado exitosamente: %s\n", filename);
    } else {
        fprintf(stderr, "Error al cambiar el fondo de pantalla\n");
    }
    
    return result;
}
