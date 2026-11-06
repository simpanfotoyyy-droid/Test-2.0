from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import warnings
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

warnings.filterwarnings("ignore")

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="BEI Advanced Stock Screener", 
    page_icon="💎", 
    layout="wide"
)

st.title("💎 BEI Advanced Stock Screener & Trading Plan")
st.caption("Pindai 900+ emiten IDX otomatis dengan filter konfirmasi 2 Candle Hijau Ekspansif + Kalkulasi SL/TP.")

# Sidebar Pengaturan
st.sidebar.header("⚙️ Pengaturan Screener")

# 1. Pilihan Mode Strategi
strategy_mode = st.sidebar.radio(
    "Pilih Mode Strategi", 
    ["🔥 Pantulan (Bounce / Support)", "🚀 Breakout (Resistance & Akumulasi)"],
    index=0
)

# 2. Pilihan Interval Waktu
interval_opt = st.sidebar.selectbox(
    "Interval Waktu (Timeframe)", 
    ["15m (15 Menit)", "1h (1 Jam)", "1d (Harian / Daily)"], 
    index=0
)

# Batasan periode dari Yahoo Finance
if "15m" in interval_opt:
    interval = "15m"
    period = "5d"
elif "1h" in interval_opt:
    interval = "1h"
    period = "60d"
else:
    interval = "1d"
    period = "1y"

min_value_rp = st.sidebar.number_input("Min. Nilai Transaksi (Rp Juta)", min_value=10, value=100) * 1_000_000

# 3. Filter Lonjakan Volume (Volume Spike Multiplier)
vol_multiplier = st.sidebar.slider(
    "Minimal Kelipatan Volume (Volume Spike)", 
    min_value=1.0, max_value=5.0, value=1.2, step=0.1,
    help="Contoh: 1.5 artinya volume harus 1.5x lebih besar dari rata-rata volume 20 periode."
)

max_workers = st.sidebar.slider("Kecepatan Scan (Threads)", min_value=4, max_value=16, value=12)

# Daftar lengkap emiten IDX
RAW_TICKERS = [
    "ROTI", "MGLV", "TRUE", "LABA", "ARCI", "IPAC", "MASB", "BMHS", "FLMC", "NICL", "UVCR", "BUKA", "HAIS", "OILS", "GPSO", "MCOL", "RSGK", "RUNS", "SBMA", "CMNT", "GTSI", "IDEA", "KUAS", "BOBA", "MTEL", "DEPO", "BINO", "CMRY", "WGSH", "TAYS", "WMPP", "RMKE", "OBMD", "AVIA", "IPPE", "NASI", "BSML", "DRMA", "ADMR", "SEMA", "ASLC", "NETV", "BAUT", "ENAK", "NTBK", "SMKM", "STAA", "NANO", "BIKE", "WIRG", "SICO", "GOTO", "TLDN", "MTMH", "WINR", "IBOS", "OLIV", "ASHA", "SWID", "TRGU", "ARKO", "CHEM", "DEWI", "AXIO", "KRYA", "HATM", "RCCC", "GULA", "JARR", "AMMS", "RAFI", "KKES", "ELPI", "EURO", "KLIN", "TOOL", "BUAH", "CRAB", "MEDS", "COAL", "PRAY", "CBUT", "BELI", "MKTR", "OMED", "BSBK", "PDPP", "KDTN", "ZATA", "NINE", "MMIX", "PADA", "ISAP", "VTNY", "SOUL", "ELIT", "BEER", "CBPE", "SUNI", "CBRE", "WINE", "BMBL", "PEVE", "LAJU", "FWCT", "NAYZ", "IRSX", "PACK", "VAST", "CHIP", "HALO", "KING", "PGEO", "FUTR", "HILL", "BDKR", "PTMP", "SAGE", "TRON", "CUAN", "NSSS", "GTRA", "HAJJ", "PIPA", "NCKL", "MENN", "AWAN", "MBMA", "RAAM", "DOOH", "JATI", "TYRE", "MPXL", "SMIL", "KLAS", "MAXI", "VKTR", "RELF", "AMMN", "CRSN", "GRPM", "WIDI", "TGUK", "INET", "MAHA", "RMKO", "CNMA", "FOLK", "HBAT", "GRIA", "PPRI", "ERAL", "CYBR", "MUTU", "LMAX", "HUMI", "MSIE", "RSCH", "BABY", "AEGS", "IOTF", "KOCI", "PTPS", "BREN", "STRK", "KOKA", "LOPI", "UDNG", "RGAS", "MSTI", "IKPM", "AYAM", "SURI", "ASLI", "CGAS", "NICE", "MSJA", "SMLE", "ACRO", "MANG", "GRPH", "SMGA", "UNTD", "TOSK", "MPIX", "ALII", "MKAP", "MEJA", "LIVE", "HYGN", "BAIK", "VISI", "AREA", "MHKI", "ATLA", "DATA", "SOLA", "BATR", "SPRE", "PART", "GOLF", "ISEA", "BLES", "GUNA", "LABS", "DOSS", "NEST", "PTMR", "VERN", "DAAZ", "BOAT", "NAIK", "AADI", "MDIY", "KSIX", "RATU", "YOII", "HGII", "BRRC", "DGWG", "CBDK", "OBAT", "MINE", "KAQI", "YUPI", "FORE", "MDLA", "DKHH", "ASPR", "PSAT", "COIN", "CDIA", "BLOG", "MERI", "CHEK", "PMUI", "EMAS", "PJHB", "RLCO", "SUPA", "WBSA", "JECX", "JELI", "EMMI", "BACH", "PRDL", "RANS", "AALI", "ABBA", "ABDA", "ABMM", "ACES", "ACST", "ADES", "ADHI", "ADMF", "ADMG", "ADRO", "AGII", "AGRO", "AGRS", "AHAP", "CASH", "TECH", "BSSR", "BSWD", "BTEK", "BTEL", "BTON", "BTPN", "BUDI", "AIMS", "AISA", "AKKU", "AKPI", "AKRA", "AKSI", "ALDO", "ALKA", "ALMI", "ALTO", "AMAG", "AMFG", "AMIN", "AMRT", "ANJT", "ANTM", "APEX", "APIC", "APII", "APLI", "APLN", "ARGO", "ARII", "ARNA", "ARTA", "ARTI", "ARTO", "ASBI", "ASDM", "ASGR", "ASII", "ASJT", "ASMI", "ASRI", "ASRM", "ASSA", "ATIC", "AUTO", "BABP", "BACA", "BAJA", "BALI", "BAPA", "BATA", "BAYU", "BBCA", "BBHI", "BBKP", "BBLD", "BBMD", "BBNI", "BBRI", "BBRM", "BBTN", "BBYB", "BCAP", "BCIC", "BCIP", "BDMN", "BEKS", "BEST", "BFIN", "BGTG", "BHIT", "BIKA", "BIMA", "BINA", "BIPI", "BIPP", "BIRD", "BISI", "BJBR", "BJTM", "BKDP", "BKSL", "BKSW", "BLTA", "BLTZ", "BMAS", "BMRI", "BMSR", "BMTR", "BNBA", "BNBR", "BNGA", "BNII", "BNLI", "BOLT", "BPFI", "BPII", "BRAM", "BRMS", "BRNA", "BRPT", "BSDE", "BSIM", "BUKK", "BULL", "BUMI", "BUVA", "BVIC", "BWPT", "BYAN", "CANI", "CASS", "CEKA", "CENT", "CFIN", "CINT", "CITA", "CLPI", "CMNP", "CMPP", "CNKO", "COWL", "CPIN", "CPRO", "CSAP", "CTBN", "CTRA", "CTTH", "DART", "DEFI", "DEWA", "DGIK", "DILD", "DKFT", "DLTA", "DMAS", "DNAR", "DNET", "DOID", "DPNS", "DSFI", "DSNG", "DSSA", "DUTI", "DVLA", "DYAN", "ECII", "EKAD", "ELSA", "ELTY", "EMDE", "EMTK", "ENRG", "EPMT", "ERAA", "ERTX", "ESSA", "ESTI", "ETWA", "EXCL", "FAST", "FASW", "FISH", "FMII", "FORU", "FPNI", "GAMA", "GDST", "GDYR", "GEMA", "GEMS", "GGRM", "GIAA", "GJTL", "GLOB", "GMTD", "GOLD", "GOLL", "GPRA", "GSMF", "GTBO", "GWSA", "GZCO", "HADE", "HDFA", "HERO", "HEXA", "HITS", "HMSP", "HOME", "HOTL", "HRUM", "IATA", "IBFN", "IBST", "ICBP", "ICON", "IGAR", "IIKP", "IKAI", "IKBI", "IMAS", "IMJS", "IMPC", "INAF", "INAI", "INCI", "INCO", "INDF", "INDR", "INDS", "INDX", "INDY", "INKP", "INPC", "INPP", "INRU", "INTA", "INTD", "INTP", "IPOL", "ISAT", "ISSP", "ITMA", "ITMG", "JAWA", "JECC", "JIHD", "JKON", "JPFA", "JRPT", "JSMR", "JSPT", "JTPE", "KAEF", "KARW", "KBLI", "KBLM", "KBLV", "KBRI", "KDSI", "KIAS", "KICI", "KIJA", "KKGI", "KLBF", "KOBX", "KOIN", "KONI", "KOPI", "KPIG", "KRAS", "KREN", "LAPD", "LCGP", "LEAD", "LINK", "LION", "LMAS", "LMPI", "LMSH", "LPCK", "LPGI", "LPIN", "LPKR", "LPLI", "LPPF", "LPPS", "LRNA", "LSIP", "LTLS", "MAGP", "MAIN", "MAPI", "MAYA", "MBAP", "MBSS", "MBTO", "MCOR", "MDIA", "MDKA", "MDLN", "MDRN", "MEDC", "MEGA", "MERK", "META", "MFMI", "MGNA", "MICE", "MIDI", "MIKA", "MIRA", "MITI", "MKPI", "MLBI", "MLIA", "MLPL", "MLPT", "MMLP", "MNCN", "MPMX", "MPPA", "MRAT", "MREI", "MSKY", "MTDL", "MTFN", "MTLA", "MTSM", "MYOH", "MYOR", "MYTX", "NELY", "NIKL", "NIRO", "NISP", "NOBU", "NRCA", "OCAP", "OKAS", "OMRE", "PADI", "PALM", "PANR", "PANS", "PBRX", "PDES", "PEGE", "PGAS", "PGLI", "PICO", "PJAA", "PKPK", "PLAS", "PLIN", "PNBN", "PNBS", "PNIN", "PNLF", "PNSE", "POLY", "POOL", "PPRO", "PSAB", "PSDN", "PSKT", "PTBA", "PTIS", "PTPP", "PTRO", "PTSN", "PTSP", "PUDP", "PWON", "PYFA", "RAJA", "RALS", "RANC", "RBMS", "RDTX", "RELI", "RICY", "RIGS", "RIMO", "RODA", "ROTI", "RUIS", "SAFE", "SAME", "SCCO", "SCMA", "SCPI", "SDMU", "SDPC", "SDRA", "SGRO", "SHID", "SIDO", "SILO", "SIMA", "SIMP", "SIPD", "SKBM", "SKLT", "SKYB", "SMAR", "SMBR", "SMCB", "SMDM", "SMDR", "SMGR", "SMMA", "SMMT", "SMRA", "SMRU", "SMSM", "SOCI", "SONA", "SPMA", "SQMI", "SRAJ", "SRIL", "SRSN", "SRTG", "SSIA", "SSMS", "SSTM", "STAR", "STTP", "SUGI", "SULI", "SUPR", "TALF", "TARA", "TAXI", "TBIG", "TBLA", "TBMS", "TCID", "TELE", "TFCO", "TGKA", "TIFA", "TINS", "TIRA", "TIRT", "TKIM", "TLKM", "TMAS", "TMPO", "TOBA", "TOTL", "TOTO", "TOWR", "TPIA", "TPMA", "TRAM", "TRIL", "TRIM", "TRIO", "TRIS", "TRST", "TRUS", "TSPC", "ULTJ", "UNIC", "UNIT", "UNSP", "UNTR", "UNVR", "VICO", "VINS", "VIVA", "VOKS", "VRNA", "WAPO", "WEHA", "WICO", "WIIM", "WIKA", "WINS", "WOMF", "WSKT", "WTON", "YPAS", "YULE", "ZBRA", "SHIP", "CASA", "DAYA", "DPUM", "IDPR", "JGLE", "KINO", "MARI", "MKNT", "MTRA", "OASA", "POWR", "INCF", "WSBP", "PBSA", "PRDA", "BOGA", "BRIS", "PORT", "CARS", "MINA", "CLEO", "TAMU", "CSIS", "TGRA", "FIRE", "TOPS", "KMTR", "ARMY", "MAPB", "WOOD", "HRTA", "MABA", "HOKI", "MPOW", "MARK", "NASA", "MDKI", "BELL", "KIOS", "GMFI", "MTWI", "ZINC", "MCAS", "PPRE", "WEGE", "PSSI", "MORA", "DWGL", "PBID", "JMAS", "CAMP", "IPCM", "PCAR", "LCKM", "BOSS", "HELI", "JSKY", "INPS", "GHON", "TDPM", "DFAM", "NICK", "BTPS", "SPTO", "PRIM", "HEAL", "TRUK", "PZZA", "TUGU", "MSIN", "SWAT", "TNCA", "MAPA", "TCPI", "IPCC", "RISE", "BPTR", "POLL", "NFCX", "MGRO", "NUSA", "FILM", "ANDI", "LAND", "MOLI", "PANI", "DIGI", "CITY", "SAPX", "SURE", "HKMU", "MPRO", "DUCK", "GOOD", "SKRN", "YELO", "CAKK", "SATU", "SOSS", "DEAL", "POLA", "DIVA", "LUCK", "URBN", "SOTS", "ZONE", "PEHA", "FOOD", "BEEF", "POLI", "CLAY", "NATO", "JAYA", "COCO", "MTPS", "CPRI", "HRME", "POSA", "JAST", "FITT", "BOLA", "CCSI", "SFAN", "POLU", "KJEN", "KAYU", "ITIC", "PAMG", "IPTV", "BLUE", "ENVY", "EAST", "LIFE", "FUJI", "KOTA", "INOV", "ARKA", "SMKL", "HDIT", "KEEN", "BAPI", "TFAS", "GGRP", "OPMS", "NZIA", "SLIS", "PURE", "IRRA", "DMMX", "SINI", "WOWS", "ESIP", "TEBE", "KEJU", "PSGO", "AGAR", "IFSH", "REAL", "IFII", "PMJS", "UCID", "GLVA", "PGJO", "AMAR", "CSRA", "INDO", "AMOR", "TRIN", "DMND", "PURA", "PTPW", "TAMA", "IKAN", "AYLS", "DADA", "ASPI", "ESTA", "BESS", "AMAN", "CARE", "SAMF", "SBAT", "KBAG", "CBMF", "RONY", "CSMI", "BBSS", "BHAT", "EPAC", "UANG", "PGUN", "SOFA", "PPGL", "TOYS", "SGER", "TRJA", "PNGO", "SCNP", "BBSI", "KMDS", "PURI", "SOHO", "HOMI", "ROCK", "ENZO", "PLAN", "PTDU", "ATAP", "VICI", "PMMP", "WIFI", "FAPA", "DCII", "KETR", "DGNS", "UFOE", "BANK", "WMUU", "EDGE", "UNIQ", "BEBS", "SNLK", "ZYRX", "LFLO", "FIMP", "TAPG", "NPGF", "LUCY", "ADCP", "HOPE"
]
TICKERS = sorted(list(set([f"{t}.JK" if not t.endswith(".JK") else t for t in RAW_TICKERS])))

def scan_ticker(ticker):
    symbol = ticker.replace(".JK", "")
    try:
        df = yf.download(ticker, period=period, interval=interval, auto_adjust=False, progress=False, threads=False)
        if df is None or df.empty or len(df) < 30:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        required = ["Open", "High", "Low", "Close", "Volume"]
        clean_df = pd.DataFrame(index=df.index)
        for col in required:
            if col in df.columns:
                s = df[col]
                if isinstance(s, pd.DataFrame):
                    s = s.iloc[:, 0]
                clean_df[col] = pd.to_numeric(s, errors="coerce")
            else:
                return None

        clean_df = clean_df.dropna().sort_index()
        clean_df = clean_df[clean_df["Volume"] >= 0]
        clean_df = clean_df[~clean_df.index.duplicated(keep="last")]

        if len(clean_df) < 25:
            return None

        close, high, low, volume, opn = clean_df["Close"], clean_df["High"], clean_df["Low"], clean_df["Volume"], clean_df["Open"]

        # Ambil Data 2 Candle Terakhir (Candle 1 = prev / iloc[-2], Candle 2 = current / iloc[-1])
        c_close = float(close.iloc[-1])
        c_open = float(opn.iloc[-1])
        c_low = float(low.iloc[-1])
        c_vol = float(volume.iloc[-1])

        p_close = float(close.iloc[-2])
        p_open = float(opn.iloc[-2])

        # Indikator Umum
        vol_sma_20 = volume.rolling(20).mean()
        v_sma = float(vol_sma_20.iloc[-1]) if not np.isnan(vol_sma_20.iloc[-1]) else c_vol
        est_tx = c_close * c_vol

        # Filter Dasar: Transaksi Minimal & Hindari Gocap
        if est_tx < min_value_rp:
            return None
        if c_vol < (v_sma * vol_multiplier):
            return None
        if c_close <= 70: 
            return None

        # ==========================================================
        # SYARAT UTAMA WAJIB: 2 CANDLE HIJAU & EKSPANSIF (BERTURUT-TURUT)
        # ==========================================================
        is_p_green = p_close > p_open          # Candle pertama hijau
        is_c_green = c_close > c_open          # Candle kedua hijau
        
        p_body = p_close - p_open              # Besar badan candle pertama
        c_body = c_close - c_open              # Besar badan candle kedua
        
        is_expanding = c_body > p_body         # Candle kedua lebih besar dari candle pertama

        # Jika tidak memenuhi syarat 2 candle hijau ekspansif, langsung skip
        if not (is_p_green and is_c_green and is_expanding):
            return None

        # ==========================================
        # STRATEGI 1: MODE PANTULAN (BOUNCE / SUPPORT)
        # ==========================================
        if "Pantulan" in strategy_mode:
            donchian_low = low.rolling(20).min()
            p_low_val = float(donchian_low.shift(1).iloc[-1]) # Support Donchian Low sebelumnya
            
            # Kondisi: Low mendekati atau menyentuh Donchian Low (toleransi 0.5%)
            near_support = c_low <= p_low_val * 1.005

            if not near_support:
                return None

            # Trading Plan Otomatis untuk Pantulan
            stop_loss = round(p_low_val * 0.98, 2)  # 2% di bawah support
            risk = c_close - stop_loss
            take_profit = round(c_close + (risk * 2.0), 2)  # Risk Reward Ratio 1:2

            return {
                "Kode": symbol,
                "Waktu": pd.Timestamp(clean_df.index[-1]).strftime("%Y-%m-%d %H:%M" if interval != "1d" else "%Y-%m-%d"),
                "Harga Close": round(c_close, 2),
                "Sinyal": "🔥 Pantulan Support",
                "Stop Loss (SL)": stop_loss,
                "Take Profit (TP)": take_profit,
                "Volume": int(c_vol),
                "Est. Transaksi (Rp)": int(est_tx),
            }

        # ==========================================
        # STRATEGI 2: MODE BREAKOUT (RESISTANCE)
        # ==========================================
        else:
            hhv_20 = high.rolling(20).max()
            p_hhv = float(hhv_20.shift(1).iloc[-1])
            pp_hhv = float(hhv_20.shift(2).iloc[-1])
            p_cls = float(close.shift(1).iloc[-1])
            ema_20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])

            # Proxy Akumulasi Broker
            high_low_range = (high - low).replace(0, 1)
            clv = ((close - low) - (high - close)) / high_low_range
            top_broker_hist = clv * volume
            sum_tb_5 = float(top_broker_hist.rolling(5).sum().iloc[-1])
            
            cond_breakout = c_close > p_hhv
            cond_prev_below = p_cls <= pp_hhv
            cond_ema = c_close > ema_20
            cond_tb = sum_tb_5 > 0

            if not (cond_breakout and cond_prev_below and cond_ema and cond_tb):
                return None

            breakout_pct = ((c_close - p_hhv) / p_hhv) * 100
            
            # Trading Plan Otomatis untuk Breakout
            stop_loss = round(p_hhv * 0.98, 2)  # Di bawah garis breakout sebelumnya
            risk = c_close - stop_loss
            take_profit = round(c_close + (risk * 2.0), 2)

            return {
                "Kode": symbol,
                "Waktu": pd.Timestamp(clean_df.index[-1]).strftime("%Y-%m-%d %H:%M" if interval != "1d" else "%Y-%m-%d"),
                "Harga Close": round(c_close, 2),
                "Breakout (%)": round(breakout_pct, 2),
                "Sinyal": "🚀 Breakout Resistance",
                "Stop Loss (SL)": stop_loss,
                "Take Profit (TP)": take_profit,
                "Volume": int(c_vol),
                "Est. Transaksi (Rp)": int(est_tx),
            }

    except Exception:
        return None

# Tombol Eksekusi di Web
if st.button(f"🚀 MULAI SCAN ({strategy_mode})", type="primary"):
    st.info(f"Memindai {len(TICKERS)} emiten pada interval **{interval}** dengan mode **{strategy_mode}**...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    completed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_ticker, t): t for t in TICKERS}
        for future in as_completed(futures):
            completed += 1
            progress_bar.progress(completed / len(TICKERS))
            status_text.text(f"Memproses {completed}/{len(TICKERS)} saham...")
            try:
                res = future.result()
                if res:
                    results.append(res)
            except Exception:
                pass

    status_text.empty()
    progress_bar.empty()

    elapsed = time.time() - start_time
    st.success(f"Pemindaian selesai dalam {elapsed:.1f} detik!")

    if results:
        res_df = pd.DataFrame(results)
        res_df = res_df.sort_values(["Harga Close"], ascending=[False]).reset_index(drop=True)
        res_df.insert(0, "Ranking", [f"🥇 Top 1" if i==0 else f"🥈 {i+1}" if i==1 else f"🥉 {i+1}" if i==2 else f"🔥 {i+1}" for i in range(len(res_df))])
        
        st.subheader(f"🎯 Hasil Screening: {strategy_mode}")
        st.dataframe(res_df, use_container_width=True)
        
        csv_data = res_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Hasil Scan (CSV)",
            data=csv_data,
            file_name=f"hasil_scanner_{interval}.csv",
            mime="text/csv",
        )
    else:
        st.warning(f"Tidak ada emiten yang memenuhi kriteria (2 Candle Hijau Ekspansif + {strategy_mode}) pada interval {interval} saat ini.")
else:
    st.write("👈 Atur mode strategi dan interval di sidebar, lalu tekan tombol **MULAI SCAN**.")
