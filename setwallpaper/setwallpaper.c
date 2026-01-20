#include <X11/Xlib.h>
#include <X11/Xatom.h>
#include <Imlib2.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Uso: %s <imagen>\n", argv[0]);
        return 1;
    }

    const char *filename = argv[1];

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
