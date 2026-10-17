package com.stickers.arabicpack;

import java.util.List;

public class StickerPack {
    public final String identifier;
    public final String name;
    public final String publisher;
    public final String trayImageFile;
    public final String imageDataVersion;
    public final boolean avoidCache;
    public final String publisherEmail;
    public final String publisherWebsite;
    public final String privacyPolicyWebsite;
    public final String licenseAgreementWebsite;
    public final List<Sticker> stickers;

    public StickerPack(String identifier, String name, String publisher, String trayImageFile,
                       String imageDataVersion, boolean avoidCache, String publisherEmail,
                       String publisherWebsite, String privacyPolicyWebsite,
                       String licenseAgreementWebsite, List<Sticker> stickers) {
        this.identifier = identifier;
        this.name = name;
        this.publisher = publisher;
        this.trayImageFile = trayImageFile;
        this.imageDataVersion = imageDataVersion;
        this.avoidCache = avoidCache;
        this.publisherEmail = publisherEmail;
        this.publisherWebsite = publisherWebsite;
        this.privacyPolicyWebsite = privacyPolicyWebsite;
        this.licenseAgreementWebsite = licenseAgreementWebsite;
        this.stickers = stickers;
    }

    public String assetPath(String fileName) {
        return identifier + "/" + fileName;
    }
}
