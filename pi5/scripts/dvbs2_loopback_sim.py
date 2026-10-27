#!/usr/bin/env python3
"""DVB-S2送受信シミュレーション: gr-dtv送信 -> 振幅・周波数ずれ・雑音 -> shonan_rxと同じ受信系。

使い方: dvbs2_loopback_sim.py MODCOD ESN0_DB [N_FRAMES]
  MODCOD は 16APSK-S_2/3 のようにGUIと同じ表記。gr-dvbs2rx(パッチ適用済み)とgr-dtvが必要。
  ロック後に受信したTSパケットに誤り・抜け・順序違いが無ければPASS。
  LDPC復号器は数フレーム単位でまとめて処理するため、最後の数フレームは出てこない(N_FRAMESは100程度)。
  結果は docs/apsk_simulation.md を参照。
"""
import sys

import numpy as np
from gnuradio import analog, blocks, dtv, dvbs2rx, filter, gr
from gnuradio.filter import firdes

SPS = 2
ROLLOFF = 0.35
TS_PKT = 188


def make_ts(n_pkts, seed=1):
    rng = np.random.default_rng(seed)
    pkts = rng.integers(0, 256, size=(n_pkts, TS_PKT), dtype=np.uint8)
    pkts[:, 0] = 0x47
    pkts[:, 1] = 0x01
    pkts[:, 2] = 0x00
    pkts[:, 3] = 0x10 | (np.arange(n_pkts) & 0x0F)
    return pkts


def tx(modulation, rate, ts_bytes):
    tb = gr.top_block()
    standard, frame_size, code_rate, constellation, rolloff, pilots = \
        dvbs2rx.params.translate('DVB-S2', 'normal', rate, modulation, ROLLOFF, True)
    src = blocks.vector_source_b(ts_bytes.tolist(), False)
    bbheader = dtv.dvb_bbheader_bb(standard, frame_size, code_rate, rolloff,
                                   dtv.INPUTMODE_NORMAL, dtv.INBAND_OFF, 168, 4000000)
    bbscrambler = dtv.dvb_bbscrambler_bb(standard, frame_size, code_rate)
    bch = dtv.dvb_bch_bb(standard, frame_size, code_rate)
    ldpc = dtv.dvb_ldpc_bb(standard, frame_size, code_rate, dtv.MOD_OTHER)
    interleaver = dtv.dvbs2_interleaver_bb(frame_size, code_rate, constellation)
    mapper = dtv.dvbs2_modulator_bc(frame_size, code_rate, constellation,
                                    dtv.INTERPOLATION_OFF)
    pl_framer = dtv.dvbs2_physical_cc(frame_size, code_rate, constellation, pilots, 0)
    taps = firdes.root_raised_cosine(SPS, SPS, 1.0, ROLLOFF, int(2 * 5 * SPS) + 1)
    rrc = filter.interp_fir_filter_ccf(1, taps)
    sink = blocks.vector_sink_c()
    tb.connect(src, bbheader, bbscrambler, bch, ldpc, interleaver, mapper,
               pl_framer, rrc, sink)
    tb.run()
    return np.array(sink.data(), dtype=np.complex64)


def rx(modulation, rate, samples):
    tb = gr.top_block()
    framesize = dvbs2rx.FECFRAME_NORMAL
    constellation = getattr(dvbs2rx, f"MOD_{modulation}")
    code_rate = getattr(dvbs2rx, "C" + rate.replace("/", "_"))
    src = blocks.vector_source_c(samples.tolist(), False)
    agc = analog.agc_cc(1e-5, 1.0, 1.0, 65536)
    rotator = dvbs2rx.rotator_cc(0.0, True)
    symbol_sync = dvbs2rx.symbol_sync_cc(SPS, 0.001, 1.0, ROLLOFF, 5, 128, 0)
    target_pls = dvbs2rx.dvbs2_pls(modulation, rate, "normal", True)
    lo, hi = dvbs2rx.pls_filter(target_pls)
    plsync = dvbs2rx.plsync_cc(0, 30, SPS, 0, False, False, lo, hi)
    demapper = dvbs2rx.xfecframe_demapper_cb(framesize, code_rate, constellation)
    ldpc = dvbs2rx.ldpc_decoder_bb(dvbs2rx.STANDARD_DVBS2, framesize, code_rate,
                                   constellation, dvbs2rx.OM_MESSAGE, dvbs2rx.INFO_OFF, 25, 0)
    bch = dvbs2rx.bch_decoder_bb(dvbs2rx.STANDARD_DVBS2, framesize, code_rate,
                                 dvbs2rx.OM_MESSAGE, 0)
    descrambler = dvbs2rx.bbdescrambler_bb(dvbs2rx.STANDARD_DVBS2, framesize, code_rate)
    deheader = dvbs2rx.bbdeheader_bb(dvbs2rx.STANDARD_DVBS2, framesize, code_rate, 0)
    sink = blocks.vector_sink_b()
    tb.connect(src, agc, rotator, symbol_sync, plsync, demapper, ldpc, bch,
               descrambler, deheader, sink)
    tb.msg_connect(plsync, "rotator_phase_inc", rotator, "cmd")
    tb.msg_connect(ldpc, "llr_pdu", demapper, "llr_pdu")
    tb.run()
    return np.array(sink.data(), dtype=np.uint8), demapper.get_snr()


def main():
    mod_cod = sys.argv[1]
    esn0_db = float(sys.argv[2])
    n_frames = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    modulation, rate = mod_cod.split("-S_")

    bits_per_sym = {"QPSK": 2, "8PSK": 3, "16APSK": 4, "32APSK": 5}[modulation]
    num, den = (int(x) for x in rate.split("/"))
    n_pkts = int(n_frames * 64800 * num / den / 8 / TS_PKT)
    pkts = make_ts(n_pkts)
    samples = tx(modulation, rate, pkts.reshape(-1))

    # Channel: gain, carrier frequency offset, phase and AWGN at the given Es/N0
    rng = np.random.default_rng(7)
    p_sig = np.mean(np.abs(samples) ** 2)
    n = np.arange(len(samples))
    cfo = 2e-4  # cycles/sample
    y = 0.3 * samples * np.exp(1j * (2 * np.pi * cfo * n + 0.7))
    sigma2 = (0.3 ** 2) * p_sig * SPS / (10 ** (esn0_db / 10))
    y = y + np.sqrt(sigma2 / 2) * (rng.standard_normal(len(y)) + 1j * rng.standard_normal(len(y)))
    y = y.astype(np.complex64)

    out, snr = rx(modulation, rate, y)
    index = {bytes(p): i for i, p in enumerate(pkts)}
    n_out = len(out) // TS_PKT
    found = [index.get(bytes(out[i * TS_PKT:(i + 1) * TS_PKT])) for i in range(n_out)]
    good = [i for i in found if i is not None]
    # Packets that match nothing before the first good one are the output of the
    # acquisition (first frames after the PL lock); only count them after that.
    first_ok = next((k for k, i in enumerate(found) if i is not None), n_out)
    bad_acq = first_ok
    bad = sum(1 for i in found[first_ok:] if i is None)
    if good:
        # From the first to the last correctly received packet, every sent packet
        # must come out once and in order (no loss inside the locked span).
        span = good[-1] - good[0] + 1
        in_order = all(b == a + 1 for a, b in zip(good, good[1:]))
        lost = span - len(good)
    else:
        span = lost = 0
        in_order = False
    verdict = "PASS" if good and bad == 0 and lost == 0 and in_order else "FAIL"
    print(f"{verdict} {mod_cod:14s} Es/N0={esn0_db:5.1f}dB sent={n_pkts:5d} locked_span={span:5d} "
          f"ok={len(good):5d} bad={bad:3d} (acq {bad_acq:3d}) lost={lost:3d} first={good[0] if good else -1} "
          f"snr_est={snr:5.1f}dB")


if __name__ == "__main__":
    main()
