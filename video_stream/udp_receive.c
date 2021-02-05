#include <glib.h>
#include <gst/gst.h>
#include <stdio.h>


int main(int argc, char** argv)
{
    GMainLoop* loop;
    GstElement* pipeline;
    GError* error = NULL;
    GstElement* src;

    char pipeline_desc[2000];
    sprintf (pipeline_desc, "\
    udpsrc port=5000 name=src \
    ! gdpdepay \
    ! rtph264depay \
    ! avdec_h264 \
    ! videoconvert \
    ! autovideosink sync=false");

    gst_init(&argc, &argv);
    loop = g_main_loop_new(NULL, FALSE);

    g_print("Creating pipeline\n");
    pipeline = gst_parse_launch(pipeline_desc, &error);
    if (error != NULL) {
        g_printerr("Error parsing '%s': %s", pipeline_desc, error->message);
        g_error_free(error);
        return -1;
    }

    gst_element_set_state(pipeline, GST_STATE_PLAYING);
    src = gst_bin_get_by_name(GST_BIN(pipeline), "src");
    if (!src) {
        g_printerr("Source element not found\n");
        return -2;
    }

    g_print("Entering main loop\n");
    g_main_loop_run(loop);

    // Exit from main loop, enter cleanup
    g_print("Exiting main loop\n");
    gst_object_unref(src);
    gst_element_set_state(pipeline, GST_STATE_NULL);
    return 0;
}