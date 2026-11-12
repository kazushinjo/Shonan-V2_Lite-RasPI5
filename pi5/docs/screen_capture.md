# 実機LCDの画面キャプチャー / Capturing the device LCD screen

(README から移した説明 / Moved from the README)

## アプリ内蔵のスクリーンショット機能(推奨) / Built-in screenshot function (recommended)

Shonan_Lite(GUI)は起動中、Unixドメインソケット`/tmp/shonan-pi5-gui.sock`でコマンドを受け付ける。
`screenshot`を送ると、表示中の画面を`/tmp/shonan_lcd_actual.png`に保存する(GUIは止まらない)。
`navigate:<画面名>`で任意の画面へ移動できる(画面名: `home` `tx` `rx` `frequency` `rssi`
`symbolrate` `fec` `modulation` `videosource` `streamoutput` `rxgain` `txpower` `manual`
`settings` `testequipment` `presets`)。
`volume:<増減>`(例: `volume:+2`)は、ロータリーエンコーダを回したときと同じ音量変更を行う(音量ポップアップの確認用)。

While running, Shonan_Lite (GUI) accepts commands on the Unix domain socket `/tmp/shonan-pi5-gui.sock`.
Sending `screenshot` saves the current screen to `/tmp/shonan_lcd_actual.png` (the GUI does not stop).
`navigate:<screen>` moves to any screen (screens: `home` `tx` `rx` `frequency` `rssi`
`symbolrate` `fec` `modulation` `videosource` `streamoutput` `rxgain` `txpower` `manual`
`settings` `testequipment` `presets`).
`volume:<delta>` (e.g. `volume:+2`) changes the volume the same way as turning the rotary encoder (for checking the volume popup).

```bash
python3 -c "import socket,sys; s=socket.socket(socket.AF_UNIX); s.connect('/tmp/shonan-pi5-gui.sock'); s.sendall(sys.argv[1].encode()); s.close()" navigate:rssi
python3 -c "import socket,sys; s=socket.socket(socket.AF_UNIX); s.connect('/tmp/shonan-pi5-gui.sock'); s.sendall(sys.argv[1].encode()); s.close()" screenshot
```

起動直後は「アプリ起動時にPlutoも再起動しています…」の表示(最大25秒)が写ることがあるので、
起動から30秒ほど待ってから撮る。

Right after startup, the message "Rebooting the Pluto as the app starts…" (up to 25 seconds) may be
captured, so wait about 30 seconds after startup before taking a screenshot.

## kmsgrabによる取得 / Capturing with kmsgrab

Shonan_LiteはLCDへQt/DRMで直接描画しているため、`/dev/fb0`を読み出す方法では
起動コンソールなど、最終合成前の内容になることがある(素の色1色などになる)。
実際にLCDへ表示されている画面を取得する場合は、KMSのCRTC/Planeを指定して
`ffmpeg`の`kmsgrab`を使う。

Because Shonan_Lite draws directly to the LCD via Qt/DRM, reading `/dev/fb0` may give content from
before final composition, such as the boot console (e.g. a single plain color). To capture what is
actually displayed on the LCD, use `ffmpeg`'s `kmsgrab` specifying the KMS CRTC/Plane.

★`/dev/dri/card0`はモードセッティング非対応のスタブデバイスで、これを指定すると
`kmsgrab`が`Failed to set universal planes capability`/`Operation not supported`
で失敗する(実機で確認)。DSIパネルを実際に駆動しているのは**`/dev/dri/card1`**
なので、必ずこちらを指定する。

★`/dev/dri/card0` is a stub device without mode-setting support; specifying it makes `kmsgrab` fail
with `Failed to set universal planes capability`/`Operation not supported` (confirmed on the device).
The DSI panel is actually driven by **`/dev/dri/card1`**, so always specify that one.

まず実機で現在のCRTC/Plane IDを確認する(再起動などでIDが変わる場合がある):

First check the current CRTC/Plane IDs on the device (the IDs may change after a reboot, etc.):

```bash
kmsprint
```

現在の実機ではCRTC IDが`36`、Plane IDが`34`なので、以下でLCD画面をPNG化できる。
`sudo`のパスワード入力が必要になる。

On the current device the CRTC ID is `36` and the Plane ID is `34`, so the following saves the LCD
screen as a PNG. You will need to enter the `sudo` password.

```bash
sudo ffmpeg -y -hide_banner \
  -f kmsgrab -device /dev/dri/card1 \
  -crtc_id 36 -plane_id 34 -framerate 1 -i - \
  -vf hwdownload,format=bgr0 -frames:v 1 -update 1 /tmp/shonan_lcd_actual.png
```

MacなどのPCへコピーする:

Copy it to a PC such as a Mac:

```bash
scp pi@<Pi5のIPアドレス / Pi 5 IP address>:/tmp/shonan_lcd_actual.png \
  ~/Desktop/shonan_lcd_actual.png
```

`/dev/fb0`の直接取得は、LCDの最終表示を取得できない場合があるため、実機LCDの
スクリーンショットには使用しない。

Reading `/dev/fb0` directly may not capture the final LCD image, so do not use it for screenshots
of the device LCD.

## Langstone V3 の画面 / The Langstone V3 screen

Langstone V3 は `/dev/fb0` に直接描画するので、Langstone 起動中はフレームバッファ(800x480、32bpp BGRA)を読めば画面を撮れる
(README のスクリーンショットもこの方法で撮った)。

Langstone V3 draws directly to `/dev/fb0`, so while it runs the screen can be captured by reading the frame buffer
(800x480, 32 bpp BGRA); the README screenshot was taken this way.

```bash
head -c $((800*480*4)) /dev/fb0 > /tmp/langstone.raw
python3 -c "from PyQt5 import QtGui; d=open('/tmp/langstone.raw','rb').read(); QtGui.QImage(d,800,480,3200,QtGui.QImage.Format_RGB32).save('/tmp/langstone.png')"
```
