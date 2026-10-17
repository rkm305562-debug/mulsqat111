package com.stickers.arabicpack;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Handler;
import android.os.Looper;
import android.util.LruCache;
import android.widget.ImageView;

import java.io.IOException;
import java.io.InputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** تحميل بسيط لصور الملصقات من assets بشكل غير متزامن مع تخزين مؤقت. */
final class ImageLoader {
    private static final ExecutorService POOL = Executors.newFixedThreadPool(3);
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static final LruCache<String, Bitmap> CACHE = new LruCache<>(80);

    private ImageLoader() {
    }

    static void load(Context context, final String path, final int size, final ImageView view) {
        final Context app = context.getApplicationContext();
        final String key = path + "@" + size;
        view.setTag(path);
        Bitmap cached = CACHE.get(key);
        if (cached != null) {
            view.setImageBitmap(cached);
            return;
        }
        view.setImageDrawable(null);
        POOL.execute(new Runnable() {
            @Override
            public void run() {
                final Bitmap bitmap = decode(app, path, size);
                if (bitmap == null) {
                    return;
                }
                CACHE.put(key, bitmap);
                MAIN.post(new Runnable() {
                    @Override
                    public void run() {
                        if (path.equals(view.getTag())) {
                            view.setImageBitmap(bitmap);
                        }
                    }
                });
            }
        });
    }

    private static Bitmap decode(Context context, String path, int size) {
        try {
            BitmapFactory.Options bounds = new BitmapFactory.Options();
            bounds.inJustDecodeBounds = true;
            try (InputStream in = context.getAssets().open(path)) {
                BitmapFactory.decodeStream(in, null, bounds);
            }
            int sample = 1;
            while (bounds.outWidth / (sample * 2) >= size) {
                sample *= 2;
            }
            BitmapFactory.Options opts = new BitmapFactory.Options();
            opts.inSampleSize = sample;
            try (InputStream in = context.getAssets().open(path)) {
                return BitmapFactory.decodeStream(in, null, opts);
            }
        } catch (IOException e) {
            return null;
        }
    }
}
