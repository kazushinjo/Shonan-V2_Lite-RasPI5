# 16APSK/32APSK受信のシミュレーション結果(2026-10-28)

`pi5/scripts/dvbs2_loopback_sim.py` で、gr-dtv(GNU Radio標準)のDVB-S2送信信号に
振幅変化(0.3倍)・周波数ずれ(2e-4 cycle/sample)・位相・白色雑音を加え、`pi5/rx/shonan_rx.py` と同じ
受信系(gr-dvbs2rx + `gr-dvbs2rx_pi5_bringup.patch` + `gr-dvbs2rx_apsk.patch`)で復調した。
ロングフレーム、パイロットあり、ロールオフ0.35、2サンプル/シンボル、100フレーム。
環境: Mac(Apple Silicon)、GNU Radio 3.10.12、gr-dvbs2rx 130c315。

PASS = ロック後に受信したTSパケットに誤り・抜け・順序違いが無い。

| MOD-COD | Es/N0(規格の必要値+約4dB) | 結果 | 受信側SNR推定 |
|---|---|---|---|
| 16APSK 2/3 | 13.0 dB | PASS | 13.5 dB |
| 16APSK 3/4 | 14.2 dB | PASS | 14.5 dB |
| 16APSK 4/5 | 15.0 dB | PASS | 15.1 dB |
| 16APSK 5/6 | 15.6 dB | PASS | 15.7 dB |
| 16APSK 8/9 | 16.9 dB | PASS | 16.9 dB |
| 16APSK 9/10 | 17.1 dB | PASS | 17.1 dB |
| 32APSK 3/4 | 16.7 dB | PASS | 17.1 dB |
| 32APSK 4/5 | 17.6 dB | PASS | 17.7 dB |
| 32APSK 5/6 | 18.3 dB | PASS | 18.3 dB |
| 32APSK 8/9 | 19.7 dB | PASS | 19.6 dB |
| 32APSK 9/10 | 20.1 dB | FAIL(22 dBでもFAIL、24 dBでPASS) | 20.0 dB |
| QPSK 1/4 | 3.0 dB | PASS | 4.4 dB |
| QPSK 8/9 | 10.4 dB | FAIL | 10.4 dB |
| QPSK 9/10 | 10.4 dB | FAIL(14 dBでもFAIL、30 dBでPASS) | 10.4 dB |
| 8PSK 3/5 | 9.5 dB | PASS | 9.6 dB |
| 8PSK 9/10 | 15.0 dB | PASS | 14.5 dB |

## 分かっていること

- QPSK 8/9・9/10の不合格は、APSKパッチを当てない版(bringupパッチのみ)でも結果が完全に同じで、
  APSK対応による変化ではない。LDPCの反復回数を25回から100回にしても変わらない。原因は未調査。
- 32APSK 9/10は他の組み合わせより約4dB多く余裕が必要。QPSK 9/10と同じ原因かは未調査。
- 実機(Pi5 + Pluto)での受信、Pi5でのCPU負荷(APSKは1シンボルごとに16点/32点との距離を計算する)は未確認。
