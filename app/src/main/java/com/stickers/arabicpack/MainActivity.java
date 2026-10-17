package com.stickers.arabicpack;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.List;

/** الشاشة الرئيسية: قائمة بحزم الملصقات. */
public class MainActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setTitle(R.string.app_name);

        List<StickerPack> loaded = null;
        try {
            loaded = StickerRepository.getPacks(this);
        } catch (RuntimeException e) {
            Toast.makeText(this, R.string.loading_failed, Toast.LENGTH_LONG).show();
            finish();
            return;
        }
        final List<StickerPack> packs = loaded;

        ListView list = new ListView(this);
        list.setAdapter(new PackAdapter(this, packs));
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                Intent intent = new Intent(MainActivity.this, PackDetailActivity.class);
                intent.putExtra(PackDetailActivity.EXTRA_PACK_ID, packs.get(position).identifier);
                startActivity(intent);
            }
        });
        setContentView(list);
    }

    private static final class PackAdapter extends BaseAdapter {
        private final Context context;
        private final List<StickerPack> packs;

        PackAdapter(Context context, List<StickerPack> packs) {
            this.context = context;
            this.packs = packs;
        }

        @Override
        public int getCount() {
            return packs.size();
        }

        @Override
        public Object getItem(int position) {
            return packs.get(position);
        }

        @Override
        public long getItemId(int position) {
            return position;
        }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            LinearLayout row;
            ImageView icon;
            TextView title;
            TextView subtitle;
            if (convertView == null) {
                int pad = Util.dp(context, 16);
                row = new LinearLayout(context);
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setGravity(Gravity.CENTER_VERTICAL);
                row.setPadding(pad, pad, pad, pad);

                icon = new ImageView(context);
                int size = Util.dp(context, 64);
                row.addView(icon, new LinearLayout.LayoutParams(size, size));

                LinearLayout texts = new LinearLayout(context);
                texts.setOrientation(LinearLayout.VERTICAL);
                LinearLayout.LayoutParams tp = new LinearLayout.LayoutParams(
                        0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
                tp.setMarginStart(pad);
                row.addView(texts, tp);

                title = new TextView(context);
                title.setTextSize(18);
                title.setTypeface(Typeface.DEFAULT_BOLD);
                title.setTextColor(Color.BLACK);
                texts.addView(title);

                subtitle = new TextView(context);
                subtitle.setTextSize(14);
                subtitle.setTextColor(Color.DKGRAY);
                texts.addView(subtitle);

                row.setTag(new View[]{icon, title, subtitle});
            } else {
                row = (LinearLayout) convertView;
            }
            View[] views = (View[]) row.getTag();
            icon = (ImageView) views[0];
            title = (TextView) views[1];
            subtitle = (TextView) views[2];

            StickerPack pack = packs.get(position);
            title.setText(pack.name);
            subtitle.setText(context.getString(R.string.stickers_count, pack.stickers.size()));
            ImageLoader.load(context, pack.assetPath(pack.trayImageFile), 96, icon);
            return row;
        }
    }
}
