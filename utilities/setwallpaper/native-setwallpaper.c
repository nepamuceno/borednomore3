/*
 * native-setwallpaper.c - X11 direct wallpaper setter with optional config sync
 *
 * Slideshow mode: animate multiple wallpapers via X11 without corrupting pcmanfm-qt.
 * Fixes BadGC errors by freeing pixmaps and images properly.
 * Only syncs config once at the end if requested.
 *
 * Author: Nepamuceno
 * Version: 2.6.0
 * License: MIT
 */

#include <X11/Xlib.h>
#include <X11/Xatom.h>
#include <Imlib2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/file.h>
#include <fcntl.h>
#include <errno.h>

#define CONFIG_PATH_TEMPLATE "%s/.config/pcmanfm-qt/lxqt/settings.conf"
#define TEMP_SUFFIX ".tmp"
#define MAX_LINE 8192

// Function prototypes
int set_wallpaper_x11(Display *dpy, Window root, const char *filename);
int update_config_silent(const char *image_path);
int file_exists(const char *path);
char* get_absolute_path(const char *path);
int run_slideshow(int argc, char **argv);

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr,
            "Usage:\n"
            "  %s <image> [--sync-config]\n"
            "  %s --slideshow <delay_seconds> <image1> <image2> ... [--sync-config]\n",
            argv[0], argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "--slideshow") == 0) {
        return run_slideshow(argc, argv);
    }

    const char *filename = argv[1];
    int sync_config = 0;

    if (argc > 2 && strcmp(argv[2], "--sync-config") == 0) {
        sync_config = 1;
    }

    if (!file_exists(filename)) {
        fprintf(stderr, "Error: File '%s' not found\n", filename);
        return 1;
    }

    Display *dpy = XOpenDisplay(NULL);
    if (!dpy) {
        fprintf(stderr, "Failed to open X11 display\n");
        return 1;
    }
    Window root = DefaultRootWindow(dpy);

    int result = set_wallpaper_x11(dpy, root, filename);
    XCloseDisplay(dpy);

    if (result != 0) {
        return result;
    }

    if (sync_config) {
        char *abs_path = get_absolute_path(filename);
        if (abs_path) {
            if (update_config_silent(abs_path) != 0) {
                fprintf(stderr, "Warning: Failed to update pcmanfm-qt config safely\n");
            }
            free(abs_path);
        }
    }

    return 0;
}

int run_slideshow(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s --slideshow <delay_seconds> <image1> <image2> ... [--sync-config]\n", argv[0]);
        return 1;
    }

    double delay = atof(argv[2]);
    int sync_config = 0;
    int last_arg = argc - 1;

    if (strcmp(argv[last_arg], "--sync-config") == 0) {
        sync_config = 1;
        argc--; // exclude flag from images
    }

    Display *dpy = XOpenDisplay(NULL);
    if (!dpy) {
        fprintf(stderr, "Failed to open X11 display\n");
        return 1;
    }
    Window root = DefaultRootWindow(dpy);

    for (int i = 3; i < argc; i++) {
        const char *filename = argv[i];
        if (!file_exists(filename)) {
            fprintf(stderr, "Skipping missing file: %s\n", filename);
            continue;
        }
        set_wallpaper_x11(dpy, root, filename);
        usleep((useconds_t)(delay * 1000000));
    }

    if (sync_config) {
        const char *last_file = argv[argc - 1];
        char *abs_path = get_absolute_path(last_file);
        if (abs_path) {
            update_config_silent(abs_path);
            free(abs_path);
        }
    }

    XCloseDisplay(dpy);
    return 0;
}

int file_exists(const char *path) {
    struct stat st;
    return (stat(path, &st) == 0 && S_ISREG(st.st_mode));
}

char* get_absolute_path(const char *path) {
    return realpath(path, NULL);
}

int set_wallpaper_x11(Display *dpy, Window root, const char *filename) {
    Imlib_Image img = imlib_load_image(filename);
    if (!img) {
        fprintf(stderr, "Failed to load image: %s\n", filename);
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
    imlib_free_image(); // free original
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

    imlib_free_image(); // free scaled image
    XFreePixmap(dpy, pix); // free pixmap to avoid BadGC

    return 0;
}

int update_config_silent(const char *image_path) {
    const char *home = getenv("HOME");
    if (!home) {
        return 1;
    }

    char config_path[MAX_LINE];
    char temp_path[MAX_LINE];
    snprintf(config_path, sizeof(config_path), CONFIG_PATH_TEMPLATE, home);
    snprintf(temp_path, sizeof(temp_path), "%s%s", config_path, TEMP_SUFFIX);

    FILE *fin = fopen(config_path, "r");
    if (!fin) {
        return 1;
    }

    FILE *fout = fopen(temp_path, "w");
    if (!fout) {
        fclose(fin);
        return 1;
    }

    int fout_fd = fileno(fout);
    if (flock(fout_fd, LOCK_EX) != 0) {
        fclose(fin);
        fclose(fout);
        return 1;
    }

    char line[MAX_LINE];
    int wallpaper_found = 0;

    while (fgets(line, sizeof(line), fin)) {
        if (strncmp(line, "Wallpaper=", 10) == 0) {
            fprintf(fout, "Wallpaper=%s\n", image_path);
            wallpaper_found = 1;
        } else {
            fputs(line, fout);
        }
    }

    if (!wallpaper_found) {
        fprintf(fout, "Wallpaper=%s\n", image_path);
    }

    fflush(fout);
    fsync(fout_fd);
    flock(fout_fd, LOCK_UN);

    fclose(fin);
    fclose(fout);

    if (rename(temp_path, config_path) != 0) {
        perror("rename");
        unlink(temp_path);
        return 1;
    }

    return 0;
}

// Shared library entry point
__attribute__((visibility("default")))
int set_wallpaper_universal(const char *image_path) {
    if (!image_path || !file_exists(image_path)) {
        return 1;
    }
    Display *dpy = XOpenDisplay(NULL);
    if (!dpy) {
        return 1;
    }
    Window root = DefaultRootWindow(dpy);
    int result = set_wallpaper_x11(dpy, root, image_path);
    XCloseDisplay(dpy);
    return result;
}
