package com.stickers.arabicpack;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** يقرأ assets/contents.json ويحتفظ بالنتيجة في الذاكرة. */
public final class StickerRepository {
    private static List<StickerPack> cache;

    private StickerRepository() {
    }

    public static synchronized List<StickerPack> getPacks(Context context) {
        if (cache == null) {
            try {
                cache = Collections.unmodifiableList(parse(readAsset(context, "contents.json")));
            } catch (IOException | JSONException e) {
                throw new IllegalStateException("Cannot read contents.json", e);
            }
        }
        return cache;
    }

    public static StickerPack findPack(Context context, String identifier) {
        if (identifier == null) {
            return null;
        }
        for (StickerPack pack : getPacks(context)) {
            if (pack.identifier.equals(identifier)) {
                return pack;
            }
        }
        return null;
    }

    private static String readAsset(Context context, String path) throws IOException {
        try (InputStream in = context.getAssets().open(path)) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) > 0) {
                out.write(buf, 0, n);
            }
            return out.toString("UTF-8");
        }
    }

    private static List<StickerPack> parse(String json) throws JSONException {
        JSONArray packsJson = new JSONObject(json).getJSONArray("sticker_packs");
        List<StickerPack> packs = new ArrayList<>();
        for (int i = 0; i < packsJson.length(); i++) {
            JSONObject p = packsJson.getJSONObject(i);
            JSONArray stickersJson = p.getJSONArray("stickers");
            List<Sticker> stickers = new ArrayList<>();
            for (int j = 0; j < stickersJson.length(); j++) {
                JSONObject s = stickersJson.getJSONObject(j);
                JSONArray emojisJson = s.getJSONArray("emojis");
                List<String> emojis = new ArrayList<>();
                for (int k = 0; k < emojisJson.length(); k++) {
                    emojis.add(emojisJson.getString(k));
                }
                stickers.add(new Sticker(s.getString("image_file"), emojis,
                        s.optString("accessibility_text", "")));
            }
            packs.add(new StickerPack(
                    p.getString("identifier"),
                    p.getString("name"),
                    p.getString("publisher"),
                    p.getString("tray_image_file"),
                    p.optString("image_data_version", "1"),
                    p.optBoolean("avoid_cache", false),
                    p.optString("publisher_email", ""),
                    p.optString("publisher_website", ""),
                    p.optString("privacy_policy_website", ""),
                    p.optString("license_agreement_website", ""),
                    stickers));
        }
        return packs;
    }
}
