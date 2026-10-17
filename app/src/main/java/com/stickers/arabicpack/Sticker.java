package com.stickers.arabicpack;

import java.util.List;

public class Sticker {
    public final String imageFile;
    public final List<String> emojis;
    public final String accessibilityText;

    public Sticker(String imageFile, List<String> emojis, String accessibilityText) {
        this.imageFile = imageFile;
        this.emojis = emojis;
        this.accessibilityText = accessibilityText;
    }
}
