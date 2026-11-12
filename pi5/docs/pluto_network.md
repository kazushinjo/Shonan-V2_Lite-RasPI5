# Plutoのネットワーク設定(USB_ETHERNET) / Pluto network settings (USB_ETHERNET)

(README から移した説明 / Moved from the README)

ADALM-Pluto(DATVファームウェア導入済み)をPi5と同じEthernetネットワークに
接続するには、あらかじめPluto側のUSB_ETHERNETインターフェースに固定IPを
設定しておく。

1. PlutoをPCとUSBケーブルで接続する(USB Mass Storageとして認識される)。
2. Plutoのドライブ直下にある`config.txt`をテキストエディタで開く。
3. `[USB_ETHERNET]`セクションの`ipaddr_eth`と`netmask_eth`を、Pi5と同じ
   サブネット内の値に設定する(例、Pi5が`192.168.0.80/24`の場合)。
4. `config.txt`を保存し、PlutoのドライブをPCから安全に取り出す(eject)。
   Plutoが自動的に再起動し、新しいIPアドレスで起動する。
5. Pi5の設定画面「送信先 (Pluto Tx)」に、ここで設定した`ipaddr_eth`の値
   (下記例では`192.168.0.51`)を入力する。

To connect the ADALM-Pluto (with DATV firmware) to the same Ethernet network as the Pi 5,
assign a static IP to the Pluto's USB_ETHERNET interface beforehand.

1. Connect the Pluto to your PC with a USB cable (it appears as a USB Mass Storage device).
2. Open `config.txt` in the root of the Pluto drive with a text editor.
3. Set `ipaddr_eth` and `netmask_eth` in the `[USB_ETHERNET]` section to values in the same subnet
   as the Pi 5 (example below for a Pi 5 at `192.168.0.80/24`).
4. Save `config.txt` and safely eject the Pluto drive from the PC.
   The Pluto reboots automatically and comes up with the new IP address.
5. Enter the `ipaddr_eth` value set here (`192.168.0.51` in the example below) into
   "Destination (Pluto Tx)" on the Pi 5 settings screen.

```ini
[USB_ETHERNET]
ipaddr_eth = 192.168.0.51
netmask_eth = 255.255.255.0
```

★Plutoのユーザー名(`root`)とパスワード(`analog`)は変更しないこと(理由は冒頭の「IMPORTANT」を参照)。

★Do not change the Pluto's username (`root`) and password (`analog`) (see "IMPORTANT" at the top for why).

★USB直結時のUSB CDCネットワーク(`[NETWORK]`セクション、既定`192.168.2.1`)
とは別の設定である。`[USB_ETHERNET]`は、Pluto(Pluto+)のUSB OTGポートに
挿したUSB-Ethernetアダプタに割り当てるIPアドレスで、これによりPlutoが
Pi5と同じLAN(Ethernet)上のノードとして直接通信できるようになる。
設定ファイルの詳細は
[ADI公式Wiki](https://wiki.analog.com/university/tools/pluto/users/customizing)
を参照。

★This is separate from the USB CDC network used for a direct USB connection (the `[NETWORK]` section,
default `192.168.2.1`). `[USB_ETHERNET]` is the IP address assigned to a USB-Ethernet adapter plugged
into the Pluto (Pluto+) USB OTG port, which lets the Pluto communicate directly as a node on the same
LAN (Ethernet) as the Pi 5. For details of the configuration file, see the
[official ADI Wiki](https://wiki.analog.com/university/tools/pluto/users/customizing).
