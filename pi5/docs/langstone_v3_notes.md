# Langstone V3 への切替・10GHz受信の詳細 / Langstone V3 switching and 10 GHz reception in detail

(README から移した詳しい説明 / Detailed notes moved from the README)

## 切替の仕組み / How switching works

Pi5起動後にまず表示される「起動するアプリを選択してください」メニュー
(`shonan-boot-menu.service`)、またはShonan_Lite Home画面の「Langstone V3」
ボタンから、[g4eml/Langstone-V3](https://github.com/g4eml/Langstone-V3)
(VHF/UHF/マイクロ波帯SDRトランシーバー、ADALM-Pluto対応)へ切り替えられる。
Langstone V3はQt eglfsとは別に`/dev/fb0`を直接描画する独立アプリのため、
DATV送受信アプリとは同時起動できないが、**`shonan-gui.service`/
`langstone.service`/`shonan-boot-menu.service`がsystemdの`Conflicts=`で
互いに排他制御されているため、Pi5自体のrebootは不要**で
`systemctl start`だけで即座に切り替わる(以前はPi5ごとrebootしていたが、
`shonan-boot-menu.service`導入により不要になった)。

- Shonan_Lite Home画面の「Langstone V3」ボタン → Langstone V3が起動
  (現在稼働中のShonan_Liteプロセスはsystemdが自動停止)
- Langstone V3の設定メニュー内「BACK TO SHONAN_LITE」ボタン →
  Shonan_Lite Home画面に戻る

From the "Select the app to start" menu shown first after the Pi 5 boots (`shonan-boot-menu.service`),
or from the "Langstone V3" button on the Shonan_Lite Home screen, you can switch to
[g4eml/Langstone-V3](https://github.com/g4eml/Langstone-V3) (a VHF/UHF/microwave SDR transceiver
supporting the ADALM-Pluto). Langstone V3 is a standalone app that draws directly to `/dev/fb0`,
separately from Qt eglfs, so it cannot run at the same time as the DATV app. However,
**`shonan-gui.service`/`langstone.service`/`shonan-boot-menu.service` are mutually exclusive via
systemd `Conflicts=`, so no reboot of the Pi 5 is needed**; a `systemctl start` switches immediately
(previously the whole Pi 5 was rebooted, but this became unnecessary with `shonan-boot-menu.service`).

- "Langstone V3" button on the Shonan_Lite Home screen → Langstone V3 starts
  (systemd automatically stops the running Shonan_Lite process)
- "BACK TO SHONAN_LITE" button in the Langstone V3 settings menu →
  returns to the Shonan_Lite Home screen

切替時にPlutoは**再起動しない**
(以前は切替のたびにPlutoを再起動しており、数十秒かかっていた)。実機試験で、
DATV→Langstone→DATVとPlutoを再起動せずに切り替えても、Langstoneの送受信と
DATVの送受信(オンデバイス復調による自局信号のロック)が正常に動くことを確認した。
ただしLangstoneは受信中にPlutoの送信LO(`altvoltage1`)をpowerdownしたまま終了し、
そのままではDATV送信の電波が出ないため、「GOTO SHONAN_LITE」で戻るときは
Langstone側とShonan_Lite側の両方で送信LOを元に戻す。
Langstoneからの切替であることは`/tmp/shonan_switch_from_langstone`で伝え、
Shonan_Liteはこれがあるときだけ起動時のPluto再起動を省く(使ったら消すので、
その後のアプリ再起動やPi5の電源投入時は従来どおり再起動する)。Langstone側の
`run_pluto`は`/tmp/langstone_goto_shonan`があるとき、終了後のPluto再起動を省く。Plutoが`fmcomms2_source: Unable to refill buffer`のように
詰まった場合は、Home画面の「アプリ再起動」(Plutoも再起動する)で復旧できる。

The Pluto is **not rebooted** when switching
(previously the Pluto was rebooted on every switch, which took tens of seconds). Device testing
confirmed that after switching DATV → Langstone → DATV without rebooting the Pluto, both Langstone
TX/RX and DATV TX/RX (locking onto the station's own signal with on-device demodulation) work
correctly. However, Langstone exits with the Pluto's TX LO (`altvoltage1`) still powered down while
receiving, which would leave DATV transmission with no RF output, so when returning via
"GOTO SHONAN_LITE" both the Langstone side and the Shonan_Lite side restore the TX LO.
A switch from Langstone is signaled by `/tmp/shonan_switch_from_langstone`, and Shonan_Lite skips the
Pluto reboot at startup only when it exists (it is deleted after use, so later app restarts and Pi 5
power-ups reboot the Pluto as before). On the Langstone side, `run_pluto` skips the Pluto reboot after
exiting when `/tmp/langstone_goto_shonan` exists. If the Pluto gets stuck, e.g. with
`fmcomms2_source: Unable to refill buffer`, it can be recovered with "Restart App" on the Home screen
(which also reboots the Pluto).

内部的には`~/.pi5_boot_mode_langstone`マーカーファイルの有無をsystemdの
`ConditionPathExists`で判定し、`shonan-gui.service`/`langstone.service`の
どちらを起動すべきかを決める(ブート時だけでなく、アプリ内からの切替時にも
マーカーを書き換えてから対象サービスを直接startする)。

Internally, systemd's `ConditionPathExists` checks for the `~/.pi5_boot_mode_langstone` marker file
to decide whether `shonan-gui.service` or `langstone.service` should start (not only at boot; when
switching from within an app, the marker is rewritten and the target service is started directly).

ウォーターフォール/スペクトラム表示は幅約512px→約790pxへ拡張済み
(FFT点数自体はGNU Radio側のfft_size=512のまま、SCALEPX()マクロで描画のみ
引き伸ばしている。帯域インジケータ・目盛り・タッチ判定も含め一貫して変換)。
横方向にはSQLボタン(x=30〜130)/Volボタン(x=660〜)と同じY帯で重なり広げる
余地が無かったため、スペクトラム欄の高さ(80→55px)とウォーターフォールの
表示履歴行数(130→90行)を縮めて表示位置を上に詰め、SQL/Vol/RITいずれとも
Y方向に重ならない帯(Y=130〜295)に収めることで横方向をほぼ画面全幅まで
広げた(実機で確認、詳細は下記パッチ参照)。
詳細は
[`pi5/docs/patches/langstone_v3_shonan_lite.patch`](patches/langstone_v3_shonan_lite.patch)
(upstream差分)を参照。

The waterfall/spectrum display has been widened from about 512 px to about 790 px
(the number of FFT points stays at fft_size=512 on the GNU Radio side; only the drawing is stretched
by the SCALEPX() macro, applied consistently to the bandwidth indicator, scale and touch detection).
Since there was no room to widen it horizontally in the same Y band as the SQL button (x=30–130) and
Vol button (x=660–), the spectrum area height (80 → 55 px) and the number of waterfall history rows
(130 → 90) were reduced and the display moved up, fitting it into a band (Y=130–295) that does not
overlap SQL/Vol/RIT vertically, which allows it to extend to nearly the full screen width (confirmed
on the device). For details, see
[`pi5/docs/patches/langstone_v3_shonan_lite.patch`](patches/langstone_v3_shonan_lite.patch)
(diff against upstream).

起動直後の受信設定の取りこぼしも修正済み。本家のGUIは、GNU Radioフローグラフが
受信設定用のFIFO(`/tmp/langstoneTRx`)を開く前にモード・フィルタ・オフセット等を送り、
届かなかった分を捨てていた。そのためフローグラフが初期値(USB・オフセット0等)のまま動き、
Sメーター・ノイズレベルが本来より高く出ることがあった(Shonan_Liteから切り替えた直後に
S2前後、MODEやBANDを操作し直すとS0になる、を実機で確認)。オフセット0ではLO直上に出る
PlutoのDC成分(DCのこぶ)を受信帯域内で拾うためで、正しい値はS0の方
(本来はLOを+50 kHzずらしてDC成分を避ける。TX→40 dBアッテネータ→RXの無信号状態でS0)。
起動時にフローグラフがFIFOを開くまで(最大20秒)待ってから設定を送るようにした
(`waitForFlowgraph()`)。なおSメーターの0点(`S-Meter Zero`)は既定値-80のままで、
絶対レベル(S9=-73 dBm等)としては未校正。

The loss of receive settings right after startup has also been fixed. The upstream GUI sent the mode,
filters, offset, etc. before the GNU Radio flowgraph opened its settings FIFO (`/tmp/langstoneTRx`)
and discarded whatever could not be delivered, so the flowgraph kept running with its defaults
(USB, offset 0, etc.) and the S-meter and noise level could read higher than they should (confirmed
on the device: about S2 right after switching from Shonan_Lite, S0 after pressing MODE or BAND again).
With offset 0 the receiver picks up the Pluto's DC component (the DC hump right at the LO) inside the
passband, so S0 is the correct reading (normally the LO is shifted by +50 kHz to avoid the DC
component; with TX → 40 dB attenuator → RX and no signal it reads S0).
At startup it now waits until the flowgraph opens the FIFO (up to 20 s) before sending the settings
(`waitForFlowgraph()`). Note that the S-meter zero (`S-Meter Zero`) is still at its default of -80,
so it is not calibrated as an absolute level (e.g. S9 = -73 dBm).

`g4eml/Langstone-V3`本家が更新された場合、`pi5/third_party/Langstone-V3/`を
直接上書きすると上記の改造が失われる。
[`pi5/scripts/update_langstone_from_upstream.sh`](../scripts/update_langstone_from_upstream.sh)
を実行すると、本家を読み取り専用でclone → このパッチを適用 →
成功した場合のみ`pi5/third_party/Langstone-V3/`を置き換える(本家への
書き込みは一切行わない)。パッチが当たらない場合は改造箇所と本家の変更が
衝突しているため、エラーで止まり手動マージが必要になる。

When upstream `g4eml/Langstone-V3` is updated, overwriting `pi5/third_party/Langstone-V3/` directly
would lose the modifications above. Running
[`pi5/scripts/update_langstone_from_upstream.sh`](../scripts/update_langstone_from_upstream.sh)
clones upstream read-only → applies this patch → replaces `pi5/third_party/Langstone-V3/` only if
that succeeds (nothing is ever written to upstream). If the patch does not apply, the modifications
conflict with upstream changes; it stops with an error and a manual merge is required.

### 10GHz受信(LNB) — Home画面の衛星をタップ / 10 GHz reception (LNB) — tap the satellite on the Home screen

Home画面の背景右側の衛星をタップすると、Langstone V3を**10GHz受信用のバンド**で
開く(普通の「Langstone」カードと同じく、Plutoは再起動しない)。アンテナ側で
**LNB(局部発振 9750 MHz)**により周波数を下げて受信する前提の設定で、
LangstoneのトランスバーターのオフセットとしてLNBの局部発振周波数を設定している。

Tapping the satellite on the right side of the Home screen background opens Langstone V3 on a
**band for 10 GHz reception** (as with the normal "Langstone" card, the Pluto is not rebooted).
The settings assume the frequency is down-converted at the antenna by an **LNB (local oscillator
9750 MHz)**, and the LNB local oscillator frequency is set as Langstone's transverter offset.

| 項目 / Item | 値 / Value |
| --- | --- |
| 画面の表示周波数<br>Displayed frequency | 10236.500 MHz(10.2365 GHz、画面に「XVTR」と表示)<br>10236.500 MHz (10.2365 GHz, "XVTR" shown on screen) |
| Plutoの受信周波数<br>Pluto receive frequency | 486.5 MHz(= 10236.5 − 9750) |
| 受信オフセット<br>Receive offset | −9750 MHz(LNB 局部発振 9750 MHz)<br>−9750 MHz (LNB local oscillator 9750 MHz) |
| 受信モード<br>Receive mode | 固定しない(Langstoneの「MODE」でUSB/FM/CW等を選べる)<br>Not fixed (USB/FM/CW etc. can be selected with Langstone's "MODE") |
| 送信<br>Transmit | **不可**(受信専用)<br>**Not possible** (receive only) |

- Langstoneの24バンドのうち、通常使われない最後のバンド(番号23、画面上は24番目)を
  このために使う。衛星をタップするたびに、Shonan_Liteが`~/Langstone/Langstone_Pluto.conf`
  のこのバンドを上の値に設定し直してから開く([`pi5/gui/langstone_config.py`](../gui/langstone_config.py))。
- 486.5 MHzはアマチュアバンド外のため、このバンドは**受信専用**
  (設定ファイルの`bandRxOnly23 1`、Langstone側の改造)。画面のPTT・ハードウェアPTT・
  CWキー・ビーコンのいずれでも送信せず。
  PTTボタンは灰色の「RX ONLY」表示になり、Plutoの送信LOも停止させる。
- 普通の「Langstone」カードで開いたときは、衛星から開く前に使っていたバンドに戻して開く
  (Langstone上で別のバンドに切り替えていた場合は、そのバンドのまま)。
- LNBへの電源供給(同軸経由のバイアスT、12〜18 V)はShonan_Lite/Langstoneでは扱わない。
  別途用意すること。
- Shonan_Lite(DATV)で10GHzをLNB受信する場合は、衛星ではなく周波数画面の「10GHz帯」を押し、
  「LNBを使用しますか?」で「はい」を選ぶ(表示10.2365 GHz、Pluto受信486.5 MHz、受信専用で送信不可。
  受信画面・RSSI測定もPluto受信周波数で動作する)。他のバンドを選ぶとLNBは解除される。

<!-- English -->

- Of Langstone's 24 bands, the last one, which is not normally used (number 23, the 24th on screen),
  is used for this. Every time the satellite is tapped, Shonan_Lite resets this band in
  `~/Langstone/Langstone_Pluto.conf` to the values above before opening
  ([`pi5/gui/langstone_config.py`](../gui/langstone_config.py)).
- Because 486.5 MHz is outside the amateur bands, this band is **receive only**
  (`bandRxOnly23 1` in the configuration file, a modification on the Langstone side). It does not
  transmit from the on-screen PTT, hardware PTT, CW key or beacon. The PTT button is shown grayed out as "RX ONLY", and the
  Pluto's TX LO is also stopped.
- When opened from the normal "Langstone" card, it returns to the band that was in use before opening
  from the satellite (if you switched to another band in Langstone, it stays on that band).
- Power for the LNB (bias-T over the coax, 12–18 V) is not handled by Shonan_Lite/Langstone.
  Provide it separately.
- To receive 10 GHz via an LNB in Shonan_Lite (DATV), press "10GHz Band" on the Frequency screen
  (not the satellite) and answer "Yes" to "Use an LNB?" (displayed 10.2365 GHz, Pluto RX 486.5 MHz,
  receive only with no transmit; the RX screen and RSSI measurement also use the Pluto RX frequency).
  Selecting another band cancels the LNB.
