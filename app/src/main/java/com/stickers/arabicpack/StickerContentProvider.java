package com.stickers.arabicpack;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.content.UriMatcher;
import android.content.res.AssetFileDescriptor;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.text.TextUtils;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.Collections;
import java.util.List;

/**
 * المزوّد الذي يقرأ منه واتساب بيانات حزم الملصقات وملفاتها.
 * الـ authority = <applicationId>.stickercontentprovider
 */
public class StickerContentProvider extends ContentProvider {
    public static final String METADATA = "metadata";
    public static final String STICKERS = "stickers";
    public static final String STICKERS_ASSET = "stickers_asset";

    private static final int METADATA_CODE = 1;
    private static final int METADATA_SINGLE_CODE = 2;
    private static final int STICKERS_CODE = 3;
    private static final int STICKERS_ASSET_CODE = 4;

    private final UriMatcher matcher = new UriMatcher(UriMatcher.NO_MATCH);
    private String authority;

    @Override
    public boolean onCreate() {
        Context context = getContext();
        if (context == null) {
            return false;
        }
        authority = context.getPackageName() + ".stickercontentprovider";
        matcher.addURI(authority, METADATA, METADATA_CODE);
        matcher.addURI(authority, METADATA + "/*", METADATA_SINGLE_CODE);
        matcher.addURI(authority, STICKERS + "/*", STICKERS_CODE);
        matcher.addURI(authority, STICKERS_ASSET + "/*/*", STICKERS_ASSET_CODE);
        return true;
    }

    @Override
    public Cursor query(Uri uri, String[] projection, String selection, String[] selectionArgs,
                        String sortOrder) {
        Context context = getContext();
        if (context == null) {
            return null;
        }
        Cursor cursor;
        switch (matcher.match(uri)) {
            case METADATA_CODE:
                cursor = packsCursor(StickerRepository.getPacks(context));
                break;
            case METADATA_SINGLE_CODE: {
                StickerPack pack = StickerRepository.findPack(context, uri.getLastPathSegment());
                cursor = packsCursor(pack == null
                        ? Collections.<StickerPack>emptyList() : Collections.singletonList(pack));
                break;
            }
            case STICKERS_CODE:
                cursor = stickersCursor(StickerRepository.findPack(context, uri.getLastPathSegment()));
                break;
            default:
                throw new IllegalArgumentException("Unknown URI: " + uri);
        }
        cursor.setNotificationUri(context.getContentResolver(), uri);
        return cursor;
    }

    private Cursor packsCursor(List<StickerPack> packs) {
        MatrixCursor cursor = new MatrixCursor(new String[]{
                "sticker_pack_identifier",
                "sticker_pack_name",
                "sticker_pack_publisher",
                "sticker_pack_icon",
                "android_play_store_link",
                "ios_app_download_link",
                "sticker_pack_publisher_email",
                "sticker_pack_publisher_website",
                "sticker_pack_privacy_policy_website",
                "sticker_pack_license_agreement_website",
                "image_data_version",
                "whatsapp_will_not_cache_stickers",
                "animated_sticker_pack"
        });
        for (StickerPack p : packs) {
            cursor.addRow(new Object[]{
                    p.identifier, p.name, p.publisher, p.trayImageFile,
                    "", "",
                    p.publisherEmail, p.publisherWebsite, p.privacyPolicyWebsite,
                    p.licenseAgreementWebsite,
                    p.imageDataVersion,
                    p.avoidCache ? 1 : 0,
                    0
            });
        }
        return cursor;
    }

    private Cursor stickersCursor(StickerPack pack) {
        MatrixCursor cursor = new MatrixCursor(new String[]{
                "sticker_file_name", "sticker_emoji", "sticker_accessibility_text"});
        if (pack != null) {
            for (Sticker s : pack.stickers) {
                cursor.addRow(new Object[]{
                        s.imageFile, TextUtils.join(",", s.emojis), s.accessibilityText});
            }
        }
        return cursor;
    }

    @Override
    public AssetFileDescriptor openAssetFile(Uri uri, String mode) throws FileNotFoundException {
        Context context = getContext();
        if (context == null || matcher.match(uri) != STICKERS_ASSET_CODE) {
            throw new FileNotFoundException("Unsupported URI: " + uri);
        }
        List<String> segments = uri.getPathSegments();
        if (segments.size() != 3) {
            throw new FileNotFoundException("Bad URI: " + uri);
        }
        String identifier = segments.get(1);
        String fileName = segments.get(2);
        StickerPack pack = StickerRepository.findPack(context, identifier);
        if (pack == null || !isKnownFile(pack, fileName)) {
            throw new FileNotFoundException("No such file: " + uri);
        }
        try {
            return context.getAssets().openFd(pack.assetPath(fileName));
        } catch (IOException e) {
            throw new FileNotFoundException("Cannot open " + uri + ": " + e.getMessage());
        }
    }

    private static boolean isKnownFile(StickerPack pack, String fileName) {
        if (fileName.equals(pack.trayImageFile)) {
            return true;
        }
        for (Sticker s : pack.stickers) {
            if (s.imageFile.equals(fileName)) {
                return true;
            }
        }
        return false;
    }

    @Override
    public String getType(Uri uri) {
        switch (matcher.match(uri)) {
            case METADATA_CODE:
                return "vnd.android.cursor.dir/vnd." + authority + "." + METADATA;
            case METADATA_SINGLE_CODE:
                return "vnd.android.cursor.item/vnd." + authority + "." + METADATA;
            case STICKERS_CODE:
                return "vnd.android.cursor.dir/vnd." + authority + "." + STICKERS;
            case STICKERS_ASSET_CODE: {
                String last = uri.getLastPathSegment();
                return last != null && last.endsWith(".png") ? "image/png" : "image/webp";
            }
            default:
                throw new IllegalArgumentException("Unknown URI: " + uri);
        }
    }

    @Override
    public Uri insert(Uri uri, ContentValues values) {
        throw new UnsupportedOperationException("Not supported");
    }

    @Override
    public int delete(Uri uri, String selection, String[] selectionArgs) {
        throw new UnsupportedOperationException("Not supported");
    }

    @Override
    public int update(Uri uri, ContentValues values, String selection, String[] selectionArgs) {
        throw new UnsupportedOperationException("Not supported");
    }
}
