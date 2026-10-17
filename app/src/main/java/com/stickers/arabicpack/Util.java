package com.stickers.arabicpack;

import android.content.Context;

final class Util {
    private Util() {
    }

    static int dp(Context context, int value) {
        return Math.round(value * context.getResources().getDisplayMetrics().density);
    }
}
