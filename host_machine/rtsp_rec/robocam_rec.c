/* GStreamer
 * Copyright (C) 2008 Wim Taymans <wim.taymans at gmail.com>
 * Copyright (C) 2015 Centricular Ltd
 *     Author: Sebastian Dröge <sebastian@centricular.com>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
 * Boston, MA 02110-1301, USA.
 */

#include <gst/gst.h>
#include <stdio.h>

#include <gst/rtsp-server/rtsp-server.h>

#define DEFAULT_RTSP_PORT "5000"

#define LATENCY 100

static char *port = (char *) DEFAULT_RTSP_PORT;

static GOptionEntry entries[] = {
  {"port", 'p', 0, G_OPTION_ARG_STRING, &port,
      "Port to listen on (default: " DEFAULT_RTSP_PORT ")", "PORT"},
  {NULL}
};

static void write_stats(gint bitrate, gint jitter) {
  FILE *fptr;

  // g_print("Writing stats\n");
  fptr = fopen("rec_stats.tmp","w");

  if(fptr == NULL)
   {
      g_warning("Unable to open file to write stats");
      return;
   }

   fprintf(fptr, "%d,%d", bitrate, jitter);
   fclose(fptr);
   return;
}


/* called when a stream has received an RTCP packet from the client */
static void
on_ssrc_active (GObject * session, GObject * source, GstRTSPMedia * media)
{
  GstStructure *stats;

  GST_INFO ("source %p in session %p is active", source, session);

  g_object_get (source, "stats", &stats, NULL);
  if (stats) {
    gchar *sstr;
    guint64 bitrate =0;
    guint jit = 0;
    gboolean is_sender = FALSE;
    gint lost = 0;

    sstr = gst_structure_to_string (stats);

    if (gst_structure_get_boolean(stats,"is-sender", &is_sender)) {
      // g_print("is-sender= %d", *is_sender);
      if (is_sender == TRUE) {
        // g_print ("structure: %s\n", sstr);
        if (gst_structure_get_uint64 (stats, "bitrate", &bitrate) &&
            gst_structure_get_uint(stats, "jitter", &jit))
        {
          // g_print("bitrate: %d\n", bitrate);
          // g_print("jitter: %d\n", jit);
          write_stats(bitrate, jit);
        }
        if (gst_structure_get_int(stats, "packets-lost", &lost)) {
          g_print("packets lost: %d\n", lost);
        }
        
      }
      // g_free(is_sender);
    }

    g_free (sstr);


    
    // if (jit != NULL) {
    //   g_free(jit);
    // }

    gst_structure_free (stats);
  }
}

static void
on_sender_ssrc_active (GObject * session, GObject * source,
    GstRTSPMedia * media)
{
  GstStructure *stats;

  GST_INFO ("source %p in session %p is active", source, session);

  // g_object_get (source, "stats", &stats, NULL);
  // if (stats) {
  //   gchar *sstr;

  //   sstr = gst_structure_to_string (stats);
  //   g_print ("Sender stats:\nstructure: %s\n", sstr);
  //   g_free (sstr);

  //   gst_structure_free (stats);
  // }
}

/* signal callback when the media is prepared for streaming. We can get the
 * session manager for each of the streams and connect to some signals. */
static void
media_prepared_cb (GstRTSPMedia * media)
{
  guint i, n_streams;

  n_streams = gst_rtsp_media_n_streams (media);

  GST_INFO ("media %p is prepared and has %u streams", media, n_streams);

  for (i = 0; i < n_streams; i++) {
    GstRTSPStream *stream;
    GObject *session;

    stream = gst_rtsp_media_get_stream (media, i);
    if (stream == NULL)
      continue;

    session = gst_rtsp_stream_get_rtpsession (stream);
    GST_INFO ("watching session %p on stream %u", session, i);

    g_signal_connect (session, "on-ssrc-active",
        (GCallback) on_ssrc_active, media);
    g_signal_connect (session, "on-sender-ssrc-active",
        (GCallback) on_sender_ssrc_active, media);
  }
}

static void
media_configure_cb (GstRTSPMediaFactory * factory, GstRTSPMedia * media)
{
  /* connect our prepared signal so that we can see when this media is
   * prepared for streaming */
  g_signal_connect (media, "prepared", (GCallback) media_prepared_cb, factory);
}

int
main (int argc, char *argv[])
{
  GMainLoop *loop;
  GstRTSPServer *server;
  GstRTSPMountPoints *mounts;
  GstRTSPMediaFactory *factory;
  GOptionContext *optctx;
  GError *error = NULL;

  optctx = g_option_context_new ("<launch line> - Test RTSP Server, Launch\n\n"
      "Example: \"( decodebin name=depay0 ! autovideosink )\"");
  g_option_context_add_main_entries (optctx, entries, NULL);
  g_option_context_add_group (optctx, gst_init_get_option_group ());
  if (!g_option_context_parse (optctx, &argc, &argv, &error)) {
    g_printerr ("Error parsing options: %s\n", error->message);
    g_option_context_free (optctx);
    g_clear_error (&error);
    return -1;
  }

  if (argc < 2) {
    g_print ("%s\n", g_option_context_get_help (optctx, TRUE, NULL));
    return 1;
  }
  g_option_context_free (optctx);

  loop = g_main_loop_new (NULL, FALSE);

  /* create a server instance */
  server = gst_rtsp_server_new ();
  // gst_rtsp_server_set_service(server,"5001");  //tharu:set the port number

  g_object_set (server, "service", port, NULL);

  /* get the mount points for this server, every server has a default object
   * that be used to map uri mount points to media factories */
  mounts = gst_rtsp_server_get_mount_points (server);

  /* make a media factory for a test stream. The default media factory can use
   * gst-launch syntax to create pipelines.
   * any launch line works as long as it contains elements named depay%d. Each
   * element with depay%d names will be a stream */
  factory = gst_rtsp_media_factory_new ();
  gst_rtsp_media_factory_set_transport_mode (factory,
      GST_RTSP_TRANSPORT_MODE_RECORD);
  gst_rtsp_media_factory_set_launch (factory, argv[1]);
  // gst_rtsp_media_factory_set_launch (factory, PIPELINE);
  gst_rtsp_media_factory_set_latency (factory, LATENCY); //tharu:lowered latency

  g_signal_connect (factory, "media-configure", (GCallback) media_configure_cb,factory);

  /* attach the test factory to the /test url */
  gst_rtsp_mount_points_add_factory (mounts, "/test", factory);

  /* don't need the ref to the mapper anymore */
  g_object_unref (mounts);

  /* attach the server to the default maincontext */
  gst_rtsp_server_attach (server, NULL);

  /* start serving */
  g_print ("stream ready at rtsp://127.0.0.1:%s/test\n", port);
  g_print ("On the sender, send a stream with rtspclientsink:\n"
      "  gst-launch-1.0 videotestsrc ! x264enc ! rtspclientsink location=rtsp://127.0.0.1:%s/test\n",
      port);
  g_main_loop_run (loop);

  return 0;
}
