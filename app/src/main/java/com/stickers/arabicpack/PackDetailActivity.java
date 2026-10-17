package com.stickers.arabicpack;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.util.DisplayMetrics;
import android.view.MenuItem;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AbsListView;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

/** تفاصيل حزمة: شبكة الملصقات وزر الإضافة إلى واتساب. */
public class PackDetailActivity extends Activity {
    public static final String EXTRA_PACK_ID = "pack_id";

    private static final int REQUEST_ADD_PACK = 200;
    private static final String WHATSAPP = "com.whatsapp";
    private static final String WHATSAPP_BUSINESS = "com.whatsapp.w4b";
    private static final int COLUMNS = 4;

    private StickerPack pack;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        pack = StickerRepository.findPack(this, getIntent().getStringExtra(EXTRA_PACK_ID));
        if (pack == null) {
            finish();
            return;
        }
        setTitle(pack.name);
        if (getActionBar() != null) {
            getActionBar().setDisplayHomeAsUpEnabled(true);
        }

        int pad = Util.dp(this, 16);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.VERTICAL);
        header.setPadding(pad, pad, pad, pad / 2);
        root.addView(header, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView title = new TextView(this);
        title.setText(pack.name);
        title.setTextSize(22);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.BLACK);
        header.addView(title);

        TextView sub = new TextView(this);
        sub.setText(pack.publisher + " \u2022 " + getString(R.string.stickers_count, pack.stickers.size()));
        sub.setTextColor(Color.DKGRAY);
        header.addView(sub);

        Button add = new Button(this);
        add.setText(R.string.add_to_whatsapp);
        add.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                addToWhatsApp();
            }
        });
        LinearLayout.LayoutParams bp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        bp.topMargin = pad / 2;
        header.addView(add, bp);

        DisplayMetrics dm = getResources().getDisplayMetrics();
        final int cell = dm.widthPixels / COLUMNS;
        GridView grid = new GridView(this);
        grid.setNumColumns(COLUMNS);
        grid.setAdapter(new BaseAdapter() {
            @Override
            public int getCount() {
                return pack.stickers.size();
            }

            @Override
            public Object getItem(int position) {
                return pack.stickers.get(position);
            }

            @Override
            public long getItemId(int position) {
                return position;
            }

            @Override
            public View getView(int position, View convertView, ViewGroup parent) {
                ImageView view = convertView instanceof ImageView
                        ? (ImageView) convertView : new ImageView(PackDetailActivity.this);
                int p = Util.dp(PackDetailActivity.this, 6);
                view.setLayoutParams(new AbsListView.LayoutParams(cell, cell));
                view.setPadding(p, p, p, p);
                view.setScaleType(ImageView.ScaleType.FIT_CENTER);
                Sticker sticker = pack.stickers.get(position);
                view.setContentDescription(sticker.accessibilityText);
                ImageLoader.load(PackDetailActivity.this, pack.assetPath(sticker.imageFile), 192, view);
                return view;
            }
        });
        root.addView(grid, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        setContentView(root);
    }

    private void addToWhatsApp() {
        boolean consumer = isInstalled(WHATSAPP);
        boolean business = isInstalled(WHATSAPP_BUSINESS);
        if (!consumer && !business) {
            Toast.makeText(this, R.string.whatsapp_missing, Toast.LENGTH_LONG).show();
            return;
        }
        Intent intent = new Intent("com.whatsapp.intent.action.ENABLE_STICKER_PACK");
        intent.putExtra("sticker_pack_id", pack.identifier);
        intent.putExtra("sticker_pack_authority", getPackageName() + ".stickercontentprovider");
        intent.putExtra("sticker_pack_name", pack.name);
        try {
            if (consumer && business) {
                startActivityForResult(
                        Intent.createChooser(intent, getString(R.string.add_to_whatsapp)), REQUEST_ADD_PACK);
            } else {
                intent.setPackage(consumer ? WHATSAPP : WHATSAPP_BUSINESS);
                startActivityForResult(intent, REQUEST_ADD_PACK);
            }
        } catch (ActivityNotFoundException e) {
            Toast.makeText(this, R.string.whatsapp_error, Toast.LENGTH_LONG).show();
        }
    }

    private boolean isInstalled(String packageName) {
        try {
            getPackageManager().getPackageInfo(packageName, 0);
            return true;
        } catch (PackageManager.NameNotFoundException e) {
            return false;
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_ADD_PACK && resultCode == RESULT_CANCELED && data != null) {
            String error = data.getStringExtra("validation_error");
            if (error != null) {
                Toast.makeText(this, getString(R.string.add_failed, error), Toast.LENGTH_LONG).show();
            }
        }
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (item.getItemId() == android.R.id.home) {
            finish();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }
}
