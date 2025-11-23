# technical_indicators.py

import pandas as pd
import numpy as np
from math import sqrt

def SMA(ohlc, period=14, column="Close"):
    """Simple Moving Average"""
    return pd.Series(ohlc[column].rolling(window=period).mean(), name=f"SMA_{period}")

def SMM(ohlc, period= 9, column= "Close"):
        """
        Simple moving median, an alternative to moving average. SMA, when used to estimate the underlying trend in a time series,
        is susceptible to rare events such as rapid shocks or other anomalies. A more robust estimate of the trend is the simple moving median over n time periods.
        """

        return pd.Series(
            ohlc[column].rolling(window=period).median(),
            name="{0} period SMM".format(period),
        )

def SSMA(ohlc,period = 9, column = "Close",adjust = True):
        """
        Smoothed simple moving average.

        :param ohlc: data
        :param period: range
        :param column: open/close/high/low column of the DataFrame
        :return: result Series
        """

        return pd.Series(
            ohlc[column]
            .ewm(ignore_na=False, alpha=1.0 / period, min_periods=0, adjust=adjust)
            .mean(),
            name="{0} period SSMA".format(period),
        )

def EMA(ohlc, period=14, column="Close", adjust=True):
    """Exponential Moving Average"""
    return pd.Series(ohlc[column].ewm(span=period, adjust=adjust).mean(), name=f"EMA_{period}")


def DEMA(ohlc,period = 9,column = "Close",adjust = True):
        """
        Double Exponential Moving Average - attempts to remove the inherent lag associated to Moving Averages
         by placing more weight on recent values. The name suggests this is achieved by applying a double exponential
        smoothing which is not the case. The name double comes from the fact that the value of an EMA (Exponential Moving Average) is doubled.
        To keep it in line with the actual data and to remove the lag the value 'EMA of EMA' is subtracted from the previously doubled EMA.
        Because EMA(EMA) is used in the calculation, DEMA needs 2 * period -1 samples to start producing values in contrast to the period
        samples needed by a regular EMA
        """

        DEMA = (
            2 * EMA(ohlc, period)
            - EMA(ohlc, period).ewm(span=period, adjust=adjust).mean()
        )

        return pd.Series(DEMA, name="{0} period DEMA".format(period))

def TEMA(ohlc, period = 9, adjust = True):
        """
        Triple exponential moving average - attempts to remove the inherent lag associated to Moving Averages by placing more weight on recent values.
        The name suggests this is achieved by applying a triple exponential smoothing which is not the case. The name triple comes from the fact that the
        value of an EMA (Exponential Moving Average) is triple.
        To keep it in line with the actual data and to remove the lag the value 'EMA of EMA' is subtracted 3 times from the previously tripled EMA.
        Finally 'EMA of EMA of EMA' is added.
        Because EMA(EMA(EMA)) is used in the calculation, TEMA needs 3 * period - 2 samples to start producing values in contrast to the period samples
        needed by a regular EMA.
        """

        triple_ema = 3 * EMA(ohlc, period)
        ema_ema_ema = (
            EMA(ohlc, period)
            .ewm(ignore_na=False, span=period, adjust=adjust)
            .mean()
            .ewm(ignore_na=False, span=period, adjust=adjust)
            .mean()
        )

        TEMA = (
            triple_ema
            - 3 * EMA(ohlc, period).ewm(span=period, adjust=adjust).mean()
            + ema_ema_ema
        )

        return pd.Series(TEMA, name="{0} period TEMA".format(period))

def TRIMA(ohlc, period = 18,column="Close"):
        """
        The Triangular Moving Average (TRIMA) [also known as TMA] represents an average of prices,
        but places weight on the middle prices of the time period.
        The calculations double-smooth the data using a window width that is one-half the length of the series.
        source: https://www.thebalance.com/triangular-moving-average-tma-description-and-uses-1031203
        """

        weights = np.concatenate([np.arange(1, period // 2 + 1), np.arange(period // 2, 0, -1)])
        weights = weights / weights.sum()
        def triangular(x):
            return np.dot(x, weights)
        return pd.Series(ohlc[column].rolling(period).apply(triangular, raw=True), name=f"TRIMA_{period}")

def TRIX(ohlc,period = 20,column = "Close",adjust = True):
        """
        The TRIX indicator calculates the rate of change of a triple exponential moving average.
        The values oscillate around zero. Buy/sell signals are generated when the TRIX crosses above/below zero.
        A (typically) 9 period exponential moving average of the TRIX can be used as a signal line.
        A buy/sell signals are generated when the TRIX crosses above/below the signal line and is also above/below zero.

        The TRIX was developed by Jack K. Hutson, publisher of Technical Analysis of Stocks & Commodities magazine,
        and was introduced in Volume 1, Number 5 of that magazine.
        """

        data = ohlc[column]

        def _ema(data, period, adjust):
            return pd.Series(data.ewm(span=period, adjust=adjust).mean())

        m = _ema(_ema(_ema(data, period, adjust), period, adjust), period, adjust)

        return pd.Series(100 * (m.diff() / m), name="{0} period TRIX".format(period))

def VAMA(ohlcv,period = 8, column = "Close",colvol="Volume"):
        """
        Volume Adjusted Moving Average
        """

        vp = ohlcv[colvol] * ohlcv[column]
        volsum = ohlcv[colvol].rolling(window=period).mean()
        volRatio = pd.Series(vp / volsum, name="VAMA")
        cumSum = (volRatio * ohlcv[column]).rolling(window=period).sum()
        cumDiv = volRatio.rolling(window=period).sum()

        return pd.Series(cumSum / cumDiv, name="{0} period VAMA".format(period))

def ER(ohlc, period=10, column="Close"):
    """Efficiency Ratio"""
    change = ohlc[column].diff(period).abs()
    total_change = ohlc[column].diff().abs().rolling(window=period).sum()
    return pd.Series(change / total_change, name="ER")

def KAMA(ohlc, er=10, ema_fast=2, ema_slow=30, period=20, column="Close", adjust=True):
    """Kaufman Adaptive Moving Average"""
    efficiency_ratio = ER(ohlc, er, column=column)
    fast_alpha = 2 / (ema_fast + 1)
    slow_alpha = 2 / (ema_slow + 1)
    smoothing_constant = (efficiency_ratio * (fast_alpha - slow_alpha) + slow_alpha) ** 2

    sma = ohlc[column].rolling(window=period).mean()
    kama = [float("nan")] * len(ohlc)

    # Build KAMA line
    for i in range(period, len(ohlc)):
        if np.isnan(kama[i - 1]):
            kama[i] = sma.iloc[i]
        else:
            kama[i] = kama[i - 1] + smoothing_constant.iloc[i] * (ohlc[column].iloc[i] - kama[i - 1])

    return pd.Series(kama, index=ohlc.index, name=f"{period} period KAMA")

def ZLEMA(ohlc,period = 26,adjust = True,column = "Close"):
        """ZLEMA is an abbreviation of Zero Lag Exponential Moving Average. It was developed by John Ehlers and Rick Way.
        ZLEMA is a kind of Exponential moving average but its main idea is to eliminate the lag arising from the very nature of the moving averages
        and other trend following indicators. As it follows price closer, it also provides better price averaging and responds better to price swings."""

        lag = int((period - 1) / 2)

        ema = pd.Series(
            (ohlc[column] + (ohlc[column].diff(lag))),
            name="{0} period ZLEMA.".format(period),
        )

        zlema = pd.Series(
            ema.ewm(span=period, adjust=adjust).mean(),
            name="{0} period ZLEMA".format(period),
        )

        return zlema

def WMA(ohlc, period=14, column="Close"):
    """Weighted Moving Average"""
    weights = np.arange(1, period + 1)
    def linear(w):
        def _inner(x):
            return np.dot(x, w) / w.sum()
        return _inner
    close = ohlc[column]
    return pd.Series(close.rolling(period, min_periods=period).apply(linear(weights), raw=True), name=f"WMA_{period}")

def HMA(ohlc, period=20, column="Close"):
    """Hull Moving Average"""
    half_length = int(period / 2)
    sqrt_length = int(sqrt(period))
    wma_half = WMA(ohlc, half_length, column)
    wma_full = WMA(ohlc, period, column)
    hma = WMA(pd.DataFrame({column: 2 * wma_half - wma_full}), sqrt_length, column)
    return hma.rename(f"HMA_{period}")

def EVWMA(ohlcv, period=20, column="Close", colvol="Volume"):
    """
        The eVWMA can be looked at as an approximation to the
        average price paid per share in the last n periods.

        :period: Specifies the number of Periods used for eVWMA calculation
        :column: Specifies the column used for price data
        
    """
    vol_sum = ohlcv[colvol].rolling(window=period).sum()
    x = (vol_sum - ohlcv[colvol]) / vol_sum
    y = (ohlcv[colvol] * ohlcv[column]) / vol_sum
    
    evwma = [0]
    for x, y in zip(x.fillna(0).items(), y.items()):
        if x[1] == 0 or y[1] == 0:
            evwma.append(0)
        else:
            evwma.append(evwma[-1] * x[1] + y[1])
    
    return pd.Series(evwma[1:], index=ohlcv.index, name=f"{period} period EVWMA")

def VWAP(ohlcv,colvol="Volume"):
    """
        The volume weighted average price (VWAP) is a trading benchmark used especially in pension plans.
        VWAP is calculated by adding up the dollars traded for every transaction (price multiplied by number of shares traded) and then dividing
        by the total shares traded for the day.
    """

    return pd.Series(
            ((ohlcv[colvol] * TP(ohlcv,high="High",low="Low")).cumsum()) / ohlcv[colvol].cumsum(),
            name="VWAP.",
    )

def TP(ohlc,high="High",low="Low",column="Close"):
        """Typical Price refers to the arithmetic average of the high, low, and closing prices for a given period."""

        return pd.Series((ohlc[high] + ohlc[low] + ohlc[column]) / 3, name="TP")

def FRAMA(ohlc, period=20, batch=10, column="Close", adjust=True):
    """Fractal Adaptive Moving Average"""
    assert period % 2 == 0, "FRAMA period must be even"
    c = ohlc[column].copy()
    window = batch * 2
    hh = c.rolling(batch).max()
    ll = c.rolling(batch).min()
    n1 = (hh - ll) / batch
    n2 = n1.shift(batch)
    hh2 = c.rolling(window).max()
    ll2 = c.rolling(window).min()
    n3 = (hh2 - ll2) / window
    D = (np.log(n1 + n2) - np.log(n3)) / np.log(2)
    alp = np.exp(-4.6 * (D - 1))
    alp = np.clip(alp, 0.01, 1).values
    filt = np.zeros(len(c))
    for i in range(len(c)):
        if i < window:
            filt[i] = c.iloc[i]
        else:
            filt[i] = c.iloc[i] * alp[i] + (1 - alp[i]) * filt[i - 1]
    return pd.Series(filt, index=ohlc.index, name=f"FRAMA_{period}")

def MACD(ohlc, period_fast = 12, period_slow = 26,signal = 9,column = "Close",adjust = True):
        """
        MACD, MACD Signal and MACD difference.
        The MACD Line oscillates above and below the zero line, which is also known as the centerline.
        These crossovers signal that the 12-day EMA has crossed the 26-day EMA. The direction, of course, depends on the direction of the moving average cross.
        Positive MACD indicates that the 12-day EMA is above the 26-day EMA. Positive values increase as the shorter EMA diverges further from the longer EMA.
        This means upside momentum is increasing. Negative MACD values indicates that the 12-day EMA is below the 26-day EMA.
        Negative values increase as the shorter EMA diverges further below the longer EMA. This means downside momentum is increasing.

        Signal line crossovers are the most common MACD signals. The signal line is a 9-day EMA of the MACD Line.
        As a moving average of the indicator, it...curs when the MACD turns up and crosses above the signal line.
        A bearish crossover occurs when the MACD turns down and crosses below the signal line.
        """

        EMA_fast = pd.Series(
            ohlc[column].ewm(ignore_na=False, span=period_fast, adjust=adjust).mean(),
            name="EMA_fast",
        )
        EMA_slow = pd.Series(
            ohlc[column].ewm(ignore_na=False, span=period_slow, adjust=adjust).mean(),
            name="EMA_slow",
        )
        MACD = pd.Series(EMA_fast - EMA_slow, name="MACD")
        MACD_signal = pd.Series(
            MACD.ewm(ignore_na=False, span=signal, adjust=adjust).mean(), name="SIGNAL"
        )

        return pd.concat([MACD, MACD_signal], axis=1)


def BOLLINGER(ohlc, period=20, dev=2, column="Close"):
    """Bollinger Bands"""
    sma = ohlc[column].rolling(window=period).mean()
    std = ohlc[column].rolling(window=period).std()
    upper_band = sma + std * dev
    lower_band = sma - std * dev
    return pd.DataFrame({"BB_UPPER": upper_band, "BB_LOWER": lower_band})

def STOCH(ohlc, period = 14,close="Close",high="High",low="Low"):
        """Stochastic oscillator %K
         The stochastic oscillator is a momentum indicator comparing the closing price of a security
         to the range of its prices over a certain period of time.
         The sensitivity of the oscillator to market movements is reducible by adjusting that time
         period or by taking a moving average of the result.
        """

        highest_high = ohlc[high].rolling(center=False, window=period).max()
        lowest_low = ohlc[low].rolling(center=False, window=period).min()

        STOCH = pd.Series(
            (ohlc[close] - lowest_low) / (highest_high - lowest_low) * 100,
            name="{0} period STOCH %K".format(period),
        )

        return STOCH

def STOCHD(ohlc, period = 3, stoch_period = 14,close="Close",high="High",low="Low"):
        """Stochastic oscillator %D
        STOCH%D is a 3 period simple moving average of %K.
        """

        return pd.Series(
            STOCH(ohlc, period = stoch_period,close=close,high=high,low=low).rolling(center=False, window=period).mean(),
            name="{0} period STOCH %D.".format(period),
        )

def STOCHRSI(ohlc, rsi_period=14, stoch_period=14, column="Close", adjust=True):
    """Stochastic RSI"""
    rsi = RSI(ohlc, rsi_period, column, adjust)
    min_val = rsi.rolling(window=stoch_period).min()
    max_val = rsi.rolling(window=stoch_period).max()
    stochrsi = 100 * (rsi - min_val) / (max_val - min_val)
    return pd.Series(stochrsi, name=f"STOCHRSI_{rsi_period}_{stoch_period}")

def CMO(ohlc, period=9, factor=100, column="Close", adjust=True):
    """Chande Momentum Oscillator"""
    delta = ohlc[column].diff()
    up = delta.copy()
    down = delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=period, adjust=adjust).mean()
    _loss = abs(down.ewm(com=period, adjust=adjust).mean())
    return pd.Series(factor * ((_gain - _loss) / (_gain + _loss)), name="CMO")


def EMV(ohlcv, period=14, high="High", low="Low", colvol="Volume"):
    """Ease of Movement"""
    dm = ((ohlcv[high] + ohlcv[low]) / 2) - ((ohlcv[high].shift() + ohlcv[low].shift()) / 2)
    br = (ohlcv[colvol] / 100000000) / ((ohlcv[high] - ohlcv[low]))
    emv = dm / br
    return pd.Series(emv.rolling(window=period).mean(), name="EMV")


def CHAIKIN(ohlcv, colvol="Volume", column="Close", high="High", low="Low", adjust=True):
    """Chaikin Oscillator"""
    adl = ADL(ohlcv, colvol, column, high, low)
    return pd.Series(adl.ewm(span=3, adjust=adjust).mean() - adl.ewm(span=10, adjust=adjust).mean(), name="CHAIKIN")

def ADL(ohlcv, colvol="Volume", column="Close", high="High", low="Low"):
    """Accumulation/Distribution Line"""
    clv = ((ohlcv[column] - ohlcv[low]) - (ohlcv[high] - ohlcv[column])) / (ohlcv[high] - ohlcv[low])
    clv = clv.fillna(0)
    return pd.Series((clv * ohlcv[colvol]).cumsum(), name="ADL")

def OBV(ohlcv, column="Close", colvol="Volume"):
    """On-Balance Volume"""
    obv = [0]
    for i in range(1, len(ohlcv)):
        if ohlcv[column].iloc[i] > ohlcv[column].iloc[i - 1]:
            obv.append(obv[-1] + ohlcv[colvol].iloc[i])
        elif ohlcv[column].iloc[i] < ohlcv[column].iloc[i - 1]:
            obv.append(obv[-1] - ohlcv[colvol].iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=ohlcv.index, name="OBV")



def ADX(ohlc, period=14, high="High", low="Low", close="Close", adjust=True):
    """Average Directional Index"""
    tr1 = ohlc[high] - ohlc[low]
    tr2 = abs(ohlc[high] - ohlc[close].shift())
    tr3 = abs(ohlc[low] - ohlc[close].shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(span=period, min_periods=period).mean()

    up_diff = ohlc[high].diff()
    down_diff = ohlc[low].diff()
    plus_dm = pd.Series(np.where((up_diff > down_diff) & (up_diff > 0), up_diff, 0), name="plus_dm")
    minus_dm = pd.Series(np.where((down_diff > up_diff) & (down_diff > 0), down_diff, 0), name="minus_dm")

    plus_di = 100 * (plus_dm.ewm(span=period, min_periods=period).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(span=period, min_periods=period).mean() / atr)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(span=period, min_periods=period).mean()
    return pd.Series(adx, name=f"ADX_{period}")

def EFI(ohlc, period=13, column="Close", colvol="Volume", adjust=True):
    """Elder's Force Index"""
    fi1 = pd.Series(ohlc[colvol] * ohlc[column].diff())
    return pd.Series(fi1.ewm(ignore_na=False, min_periods=9, span=10, adjust=adjust).mean(), name="EFI")


def WOBV(ohlcv, column="Close", colvol="Volume"):
    """Weighted On-Balance Volume"""
    obv = [0]
    for i in range(1, len(ohlcv)):
        delta = ohlcv[column].iloc[i] - ohlcv[column].iloc[i - 1]
        obv.append(obv[-1] + delta * ohlcv[colvol].iloc[i])
    return pd.Series(obv, index=ohlcv.index, name="WOBV")


def DMI(ohlc, period=14, high="High", low="Low", column="Close"):
    """Directional Movement Index"""
    up_diff = ohlc[high].diff()
    down_diff = ohlc[low].diff()
    plus_dm = pd.Series(np.where((up_diff > down_diff) & (up_diff > 0), up_diff, 0), name="plus_dm")
    minus_dm = pd.Series(np.where((down_diff > up_diff) & (down_diff > 0), down_diff, 0), name="minus_dm")
    tr = pd.concat([ohlc[high] - ohlc[low], abs(ohlc[high] - ohlc[column].shift()), abs(ohlc[low] - ohlc[column].shift())], axis=1).max(axis=1)
    atr = tr.ewm(span=period, min_periods=period).mean()
    plus_di = 100 * (plus_dm.ewm(span=period, min_periods=period).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(span=period, min_periods=period).mean() / atr)
    return pd.DataFrame({"+DI": plus_di, "-DI": minus_di})

def CFI(ohlcv, column="Close", colvol="Volume", adjust=True):
    """Cumulative Force Index"""
    fi1 = pd.Series(ohlcv[colvol] * ohlcv[column].diff())
    cfi = pd.Series(fi1.ewm(ignore_na=False, min_periods=9, span=10, adjust=adjust).mean(), name="CFI")
    return cfi.cumsum()

def EBBP(ohlc, period=13, high="High", low="Low", column="Close", adjust=True):
    """Elder Bull Power / Bear Power"""
    ema = ohlc[column].ewm(span=period, adjust=adjust).mean()
    bull_power = ohlc[high] - ema
    bear_power = ohlc[low] - ema
    return pd.DataFrame({"Bull": bull_power, "Bear": bear_power}, index=ohlc.index)

def ROC(ohlc, period=10, column="Close"):
    """Rate of Change"""
    return pd.Series(ohlc[column].pct_change(period) * 100, name=f"ROC_{period}")


def CCI(ohlc, period=20, high="High", low="Low", close="Close"):
    """Commodity Channel Index"""
    tp = (ohlc[high] + ohlc[low] + ohlc[close]) / 3
    sma = tp.rolling(window=period).mean()
    mean_deviation = tp.rolling(window=period).apply(lambda x: np.fabs(x - x.mean()).mean())
    cci = (tp - sma) / (0.015 * mean_deviation)
    return pd.Series(cci, name=f"CCI_{period}")

def COPP(ohlc, adjust = True):
        """The Coppock Curve is a momentum indicator, it signals buying opportunities when the indicator moved from negative territory to positive territory."""

        roc1 = ROC(ohlc, 14)
        roc2 = ROC(ohlc, 11)

        return pd.Series(
            (roc1 + roc2).ewm(span=10, min_periods=9, adjust=adjust).mean(),
            name="Coppock Curve",
        )

def VBM(ohlc, period=14, std_dev=2, column="Close"):
    """Volatility-Based Momentum"""
    volatility = ohlc[column].pct_change().rolling(window=period).std() * np.sqrt(period)
    momentum = ohlc[column].pct_change(period)
    return pd.Series(momentum / volatility, name="VBM")

def RSI(ohlc, period=14, column="Close", adjust=True):
    """Relative Strength Index"""
    delta = ohlc[column].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=period - 1, adjust=adjust).mean()
    _loss = abs(down.ewm(com=period - 1, adjust=adjust).mean())
    RS = _gain / _loss
    return pd.Series(100 - (100 / (1 + RS)), name=f"RSI_{period}")


def QSTICK(ohlc, period=10, open="Open", close="Close"):
    """Q Stick Indicator"""
    return pd.Series(ohlc[close].pct_change(period) - ohlc[open].pct_change(period), name="QSTICK")

def WTO(ohlc, channel_length=10, average_length=21, adjust=True):
    """Wave Trend Oscillator"""
    ap = (ohlc["High"] + ohlc["Low"] + ohlc["Close"]) / 3
    esa = ap.ewm(span=average_length, adjust=adjust).mean()
    d = pd.Series((ap - esa).abs().ewm(span=channel_length, adjust=adjust).mean(), name="d")
    ci = (ap - esa) / (0.015 * d)
    wt1 = pd.Series(ci.ewm(span=average_length, adjust=adjust).mean(), name="WT1.")
    wt2 = pd.Series(wt1.rolling(window=4).mean(), name="WT2.")
    return pd.concat([wt1, wt2], axis=1)

def SAR(ohlc, af = 0.02, amax = 0.2,high="High",low="Low"):
        """SAR stands for "stop and reverse," which is the actual indicator used in the system.
        SAR trails price as the trend extends over time. The indicator is below prices when prices are rising and above prices when prices are falling.
        In this regard, the indicator stops and reverses when the price trend reverses and breaks above or below the indicator."""
        high1, low1 = ohlc[high], ohlc[low]

        # Starting values
        sig0, xpt0, af0 = True, high1[0], af
        _sar = [low1[0] - (high1 - low1).std()]

        for i in range(1, len(ohlc)):
            sig1, xpt1, af1 = sig0, xpt0, af0

            lmin = min(low1[i - 1], low1[i])
            lmax = max(high1[i - 1], high1[i])

            if sig1:
                sig0 = low1[i] > _sar[-1]
                xpt0 = max(lmax, xpt1)
            else:
                sig0 = high1[i] >= _sar[-1]
                xpt0 = min(lmin, xpt1)

            if sig0 == sig1:
                sari = _sar[-1] + (xpt1 - _sar[-1]) * af1
                af0 = min(amax, af1 + af)

                if sig0:
                    af0 = af0 if xpt0 > xpt1 else af1
                    sari = min(sari, lmin)
                else:
                    af0 = af0 if xpt0 < xpt1 else af1
                    sari = max(sari, lmax)
            else:
                af0 = af
                sari = xpt0

            _sar.append(sari)

        return pd.Series(_sar, index=ohlc.index)

def PSAR(ohlc, iaf = 0.02, maxaf = 0.2,high="High",low="Low",close="Close"):
        """
        The parabolic SAR indicator, developed by J. Wells Wilder, is used by traders to determine trend direction and potential reversals in price.
        The indicator uses a trailing stop and reverse method called "SAR," or stop and reverse, to identify suitable exit and entry points.
        Traders also refer to the indicator as the parabolic stop and reverse, parabolic SAR, or PSAR.
        https://www.investopedia.com/terms/p/parabolicindicator.asp
        https://virtualizedfrog.wordpress.com/2014/12/09/parabolic-sar-implementation-in-python/
        """

        length = len(ohlc)
        high1, low1, close1 = ohlc[high], ohlc[low], ohlc[close]
        psar = close1[0 : len(close1)]
        psarbull = [None] * length
        psarbear = [None] * length
        bull = True
        af = iaf
        hp = high1[0]
        lp = low1[0]

        for i in range(2, length):
            if bull:
                psar[i] = psar[i - 1] + af * (hp - psar[i - 1])
            else:
                psar[i] = psar[i - 1] + af * (lp - psar[i - 1])

            reverse = False

            if bull:
                if low1[i] < psar[i]:
                    bull = False
                    reverse = True
                    psar[i] = hp
                    lp = low1[i]
                    af = iaf
            else:
                if high1[i] > psar[i]:
                    bull = True
                    reverse = True
                    psar[i] = lp
                    hp = high1[i]
                    af = iaf

            if not reverse:
                if bull:
                    if high1[i] > hp:
                        hp = high1[i]
                        af = min(af + iaf, maxaf)
                    if low1[i - 1] < psar[i]:
                        psar[i] = low1[i - 1]
                    if low1[i - 2] < psar[i]:
                        psar[i] = low1[i - 2]
                else:
                    if low1[i] < lp:
                        lp = low1[i]
                        af = min(af + iaf, maxaf)
                    if high1[i - 1] > psar[i]:
                        psar[i] = high1[i - 1]
                    if high1[i - 2] > psar[i]:
                        psar[i] = high1[i - 2]

            if bull:
                psarbull[i] = psar[i]
            else:
                psarbear[i] = psar[i]

        psar = pd.Series(psar, name="psar", index=ohlc.index)
        psarbear = pd.Series(psarbear, name="psarbear", index=ohlc.index)
        psarbull = pd.Series(psarbull, name="psarbull", index=ohlc.index)

        psar_df = pd.concat([psar, psarbull, psarbear], axis=1)

        return psar_df

def KST(ohlc, r1=10, r2=15, r3=20, r4=30, column="Close"):
    """Know Sure Thing"""
    r1 = ROC(ohlc, r1, column).rolling(window=10).mean()
    r2 = ROC(ohlc, r2, column).rolling(window=10).mean()
    r3 = ROC(ohlc, r3, column).rolling(window=10).mean()
    r4 = ROC(ohlc, r4, column).rolling(window=15).mean()
    k = pd.Series((r1 * 1) + (r2 * 2) + (r3 * 3) + (r4 * 4), name="KST")
    signal = pd.Series(k.rolling(window=10).mean(), name="signal")
    return pd.concat([k, signal], axis=1)

def TSI(ohlc,long = 25,short = 13,signal = 13,column = "Close",adjust = True):
        """True Strength Index (TSI) is a momentum oscillator based on a double smoothing of price changes."""

        ## Double smoother price change
        momentum = pd.Series(ohlc[column].diff())  ## 1 period momentum
        _EMA25 = pd.Series(
            momentum.ewm(span=long, min_periods=long - 1, adjust=adjust).mean(),
            name="_price change EMA25",
        )
        _DEMA13 = pd.Series(
            _EMA25.ewm(span=short, min_periods=short - 1, adjust=adjust).mean(),
            name="_price change double smoothed DEMA13",
        )

        ## Double smoothed absolute price change
        absmomentum = pd.Series(ohlc[column].diff().abs())
        _aEMA25 = pd.Series(
            absmomentum.ewm(span=long, min_periods=long - 1, adjust=adjust).mean(),
            name="_abs_price_change EMA25",
        )
        _aDEMA13 = pd.Series(
            _aEMA25.ewm(span=short, min_periods=short - 1, adjust=adjust).mean(),
            name="_abs_price_change double smoothed DEMA13",
        )

        TSI = pd.Series((_DEMA13 / _aDEMA13) * 100, name="TSI")
        signal = pd.Series(
            TSI.ewm(span=signal, min_periods=signal - 1, adjust=adjust).mean(),
            name="signal",
        )

        return pd.concat([TSI, signal], axis=1)

def FISH(ohlc, period=10, adjust=True, high="High", low="Low"):
    """Fisher Transform"""
    med = (ohlc[high] + ohlc[low]) / 2
    ndaylow = med.rolling(window=period).min()
    ndayhigh = med.rolling(window=period).max()
    raw = (2 * ((med - ndaylow) / (ndayhigh - ndaylow))) - 1
    smooth = raw.ewm(span=5, adjust=adjust).mean()
    _smooth = smooth.fillna(0)
    return pd.Series(
        np.log((1 + _smooth) / (1 - _smooth)).ewm(span=3, adjust=adjust).mean(),
        name=f"FISH_{period}"
    )

def ICHIMOKU(ohlc, kijun_period=26, tenkan_period=9, senkou_period=52, chikou_period=26,
              high="High", low="Low", close="Close", open="Open"):
    """Ichimoku Cloud"""
    tenkan_sen = (ohlc[high].rolling(window=tenkan_period).max() +
                  ohlc[low].rolling(window=tenkan_period).min()) / 2
    kijun_sen = (ohlc[high].rolling(window=kijun_period).max() +
                 ohlc[low].rolling(window=kijun_period).min()) / 2
    senkou_span_a = pd.Series(((tenkan_sen + kijun_sen) / 2).shift(kijun_period), name="SENKOU_A")
    senkou_span_b = pd.Series(((ohlc[high].rolling(window=senkou_period).max() +
                                ohlc[low].rolling(window=senkou_period).min()) / 2).shift(kijun_period), name="SENKOU_B")
    chikou_span = pd.Series(ohlc[close].shift(-chikou_period), name="CHIKOU")
    return pd.DataFrame({
        "TENKAN": tenkan_sen,
        "KIJUN": kijun_sen,
        "SENKOU_A": senkou_span_a,
        "SENKOU_B": senkou_span_b,
        "CHIKOU": chikou_span
    })


def DC(ohlc, period=20, high="High", low="Low", close="Close", adjust=True):
    """Donchian Channels"""
    upper = ohlc[high].rolling(window=period).max()
    lower = ohlc[low].rolling(window=period).min()
    middle = (upper + lower) / 2
    return pd.DataFrame({"DC_U": upper, "DC_L": lower, "DC_M": middle})



def MFI(ohlc, period=14, high="High", low="Low", close="Close", colvol="Volume"):
    """Money Flow Index"""
    tp = TP(ohlc, high=high, low=low, column=close)
    rmf = tp * ohlc[colvol]  # Raw Money Flow
    mf_sign = np.sign(tp.diff())  # Positive or negative money flow
    pos_mf = np.where(mf_sign == 1, rmf, 0)
    neg_mf = np.where(mf_sign == -1, rmf, 0)

    pos_mf_sum = pd.Series(pos_mf).rolling(window=period).sum()
    neg_mf_sum = pd.Series(neg_mf).rolling(window=period).sum()

    mfratio = pos_mf_sum / neg_mf_sum
    mfi = 100 - (100 / (1 + mfratio))

    return pd.Series(mfi, name=f"{period} period MFI")

def MOM(ohlc, period = 10, column = "Close"):
        """Market momentum is measured by continually taking price differences for a fixed time interval.
        To construct a 10-day momentum line, simply subtract the closing price 10 days ago from the last closing price.
        This positive or negative value is then plotted around a zero line."""

        return pd.Series(ohlc[column].diff(period), name="MOM".format(period))

def DYMI(ohlc, column = "Close", adjust = True):
        """
        The Dynamic Momentum Index is a variable term RSI. The RSI term varies from 3 to 30. The variable
        time period makes the RSI more responsive to short-term moves. The more volatile the price is,
        the shorter the time period is. It is interpreted in the same way as the RSI, but provides signals earlier.
        Readings below 30 are considered oversold, and levels over 70 are considered overbought. The indicator
        oscillates between 0 and 100.
        https://www.investopedia.com/terms/d/dynamicmomentumindex.asp
        """

        def _get_time(close):
            # Value available from 14th period
            sd = close.rolling(5).std()
            asd = sd.rolling(10).mean()
            v = sd / asd
            t = 14 / v.round()
            t[t.isna()] = 0
            t = t.map(lambda x: int(min(max(x, 5), 30)))
            return t

        def _dmi(index):
            time = t.iloc[index]
            if (index - time) < 0:
                subset = ohlc.iloc[0:index]
            else:
                subset = ohlc.iloc[(index - time) : index]
            return RSI(subset, period=time, column = column,adjust=adjust).values[-1]

        dates = pd.Series(ohlc.index)
        periods = pd.Series(data=range(14, len(dates)), index=ohlc.index[14:].values)
        t = _get_time(ohlc[column])
        return periods.map(lambda x: _dmi(x))

def VPT(ohlcv, colvol="Volume", column="Close", open="Open", high="High", low="Low"):
    """Volume Price Trend"""
    hilow = (ohlcv[high] - ohlcv[low]) * 100
    openclose = (ohlcv[column] - ohlcv[open]) * 100
    vol = ohlcv[colvol] / hilow
    spreadvol = (openclose * vol).cumsum()
    vpt = spreadvol + spreadvol
    return pd.Series(vpt, name="VPT")

def FVE(ohlcv, period=22, factor=0.3, colvol="Volume", column="Close", open="Open", high="High", low="Low"):
    """Fractal Volume Efficiency"""
    mf = (ohlcv[column] - ((ohlcv[high] + ohlcv[low]) / 2))
    smav = ohlcv[column].rolling(window=period).mean()
    vol_shift = pd.Series(np.where(mf > factor * ohlcv[column] / 100,
                                 ohlcv[colvol],
                                 np.where(mf < -factor * ohlcv[column] / 100,
                                          -ohlcv[colvol], 0)),
                           index=ohlcv.index)
    _sum = vol_shift.rolling(window=period).sum()
    return pd.Series((_sum / smav) / period * 100, name="FVE")

def PPO(ohlcv, fast=12, slow=26, signal=9, column="Close", colvol="Volume", adjust=True):
    """Price Percentage Oscillator"""
    _fast = ohlcv[column].ewm(span=fast, adjust=adjust).mean()
    _slow = ohlcv[column].ewm(span=slow, adjust=adjust).mean()
    ppo = pd.Series(((_fast - _slow) / _slow) * 100, name="PPO")
    signal_line = ppo.ewm(span=signal, adjust=adjust).mean()
    histogram = pd.Series(ppo - signal_line, name="PPO_histo")
    return pd.DataFrame({"PPO": ppo, "PPO_signal": signal_line, "PPO_histo": histogram})

def VW_MACD(ohlcv, period_fast=12, period_slow=26, signal=9, column="Close", colvol="Volume", adjust=True):
    """Volume Weighted MACD"""
    vp = (ohlcv[column] * ohlcv[colvol]).ewm(span=period_fast, adjust=adjust).mean()
    vslow = (ohlcv[column] * ohlcv[colvol]).ewm(span=period_slow, adjust=adjust).mean()
    vfast = (ohlcv[column] * ohlcv[colvol]).ewm(span=period_fast, adjust=adjust).mean()
    macd = pd.Series(vp - vslow, name="VW_MACD")
    signal_line = macd.ewm(span=signal, adjust=adjust).mean()
    return pd.DataFrame({"VW_MACD": macd, "Signal": signal_line})


def AO(ohlc, high="High", low="Low"):
    """Awesome Oscillator"""
    median_price = (ohlc[high] + ohlc[low]) / 2
    ao = median_price.rolling(window=5).mean() - median_price.rolling(window=34).mean()
    return pd.Series(ao, name="AO")

def MI(ohlc, period=9, adjust=True, high="High", low="Low"):
    """Mass Index"""
    _range = ohlc[high] - ohlc[low]
    EMA9 = _range.ewm(span=period, ignore_na=False, adjust=adjust).mean()
    DEMA9 = EMA9.ewm(span=period, ignore_na=False, adjust=adjust).mean()
    mass = EMA9 / DEMA9
    return pd.Series(mass.rolling(window=25).sum(), name="MI")


def PZO(ohlcv, period=14, column="Close", colvol="Volume", adjust=True):
    """Price Zone Oscillator"""
    pzo = ohlcv[column].pct_change(period)
    return pd.Series(pzo.ewm(span=period, adjust=adjust).mean(), name="PZO")

def UO(ohlc, period=14, high="High", low="Low", close="Close", column="Close"):
    """Ultimate Oscillator"""
    bp = ohlc[column] - ohlc[[low, column]].min(axis=1)
    tr = pd.concat([
        ohlc[high] - ohlc[low],
        abs(ohlc[high] - ohlc[close].shift()),
        abs(ohlc[low] - ohlc[close].shift())
    ], axis=1).max(axis=1)
    avg7 = bp.rolling(window=7).sum() / tr.rolling(window=7).sum()
    avg14 = bp.rolling(window=14).sum() / tr.rolling(window=14).sum()
    avg28 = bp.rolling(window=28).sum() / tr.rolling(window=28).sum()
    uo = (avg7 * 4 + avg14 * 2 + avg28) / (4 + 2 + 1)
    return pd.Series(uo * 100, name="UO")

def BASP(ohlc, period = 40, adjust = True,colvol="Volume",high="High",low="Low",close="Close"):
        """BASP indicator serves to identify buying and selling pressure."""

        sp = ohlc[high] - ohlc[close]
        bp = ohlc[close] - ohlc[low]
        spavg = sp.ewm(span=period, adjust=adjust).mean()
        bpavg = bp.ewm(span=period, adjust=adjust).mean()

        nbp = bp / bpavg
        nsp = sp / spavg

        varg = ohlc[colvol].ewm(span=period, adjust=adjust).mean()
        nv = ohlc[colvol] / varg

        nbfraw = pd.Series(nbp * nv, name="Buy.")
        nsfraw = pd.Series(nsp * nv, name="Sell.")

        return pd.concat([nbfraw, nsfraw], axis=1)

def BASPN(ohlcv, period=40, adjust=True, colvol="Volume", high="High", low="Low", close="Close"):
    """Normalized Buyer/Seller Pressure"""
    sp = ohlcv[high] - ohlcv[close]
    bp = ohlcv[close] - ohlcv[low]
    spavg = sp.ewm(span=period, adjust=adjust).mean()
    bpavg = bp.ewm(span=period, adjust=adjust).mean()
    nbp = bp / bpavg
    nsp = sp / spavg
    nbf = pd.Series((nbp * (ohlcv[colvol] / spavg)).ewm(span=20, adjust=adjust).mean(), name="Buy.")
    nsf = pd.Series((nsp * (ohlcv[colvol] / spavg)).ewm(span=20, adjust=adjust).mean(), name="Sell.")
    return pd.DataFrame({"BASPN_Buy": nbf, "BASPN_Sell": nsf})

def IFT_RSI(ohlc, rsi_period=5, wma_period=9, column="Close", adjust=True):
    """Inverse Fisher Transform RSI"""
    rsi = RSI(ohlc, rsi_period, column, adjust)
    v1 = pd.Series(0.1 * (rsi - 50), name="v1")
    weights = np.arange(1, wma_period + 1)
    d = (wma_period * (wma_period + 1)) / 2
    _wma = v1.rolling(wma_period, min_periods=wma_period)
    v2 = _wma.apply(lambda x: np.dot(x, weights) / d, raw=True)
    ift = pd.Series(((v2 ** 2 - 1) / (v2 ** 2 + 1)), name="IFT_RSI")
    return ift


def PIVOT(ohlc, open="Open", close="Close", high="High", low="Low"):
    """Classic Pivot Points"""
    df = ohlc.shift()
    pp = pd.Series((df[high] + df[low] + df[close]) / 3, name="pivot")
    r1 = pd.Series(2 * pp - df[low], name="r1")
    r2 = pd.Series(pp + (df[high] - df[low]), name="r2")
    r3 = pd.Series(df[high] + 2 * (pp - df[low]), name="r3")
    s1 = pd.Series(2 * pp - df[high], name="s1")
    s2 = pd.Series(pp - (df[high] - df[low]), name="s2")
    s3 = pd.Series(pp - 2 * (df[high] - df[low]), name="s3")
    return pd.concat([pp, s1, s2, s3, r1, r2, r3], axis=1)

def PIVOT_FIB(ohlc, open="Open", close="Close", high="High", low="Low"):
    """Fibonacci Pivot Points"""
    df = ohlc.shift()
    pp = pd.Series((df[high] + df[low] + df[close]) / 3, name="pivot")
    s1 = pd.Series(pp - 0.382 * (df[high] - df[low]), name="s1")
    s2 = pd.Series(pp - 0.618 * (df[high] - df[low]), name="s2")
    s3 = pd.Series(pp - 1.0 * (df[high] - df[low]), name="s3")
    r1 = pd.Series(pp + 0.382 * (df[high] - df[low]), name="r1")
    r2 = pd.Series(pp + 0.618 * (df[high] - df[low]), name="r2")
    r3 = pd.Series(pp + 1.0 * (df[high] - df[low]), name="r3")
    return pd.concat([pp, s1, s2, s3, r1, r2, r3], axis=1)

def KC(ohlc, period=20, atr_period=10, kc_mult=2, high="High", low="Low", column="Close", adjust=True):
    """Keltner Channels"""
    tp = (ohlc[high] + ohlc[low] + ohlc[column]) / 3
    kc_middle = tp.ewm(span=period, adjust=adjust).mean()
    tr = pd.concat([
        ohlc[high] - ohlc[low],
        abs(ohlc[high] - ohlc[column].shift()),
        abs(ohlc[low] - ohlc[column].shift())
    ], axis=1).max(axis=1)
    mean_dev = tr.ewm(span=atr_period, adjust=adjust).mean()
    kc_upper = kc_middle + kc_mult * mean_dev
    kc_lower = kc_middle - kc_mult * mean_dev
    return pd.DataFrame({
        "KC_MIDDLE": kc_middle,
        "KC_UPPER": kc_upper,
        "KC_LOWER": kc_lower
    })

def APZ(ohlc, period=21, dev_factor=2, column="Close", high="High", low="Low", adjust=True):
    """Adaptive Price Zone"""
    ma = ohlc[column].ewm(span=period, adjust=adjust).mean()
    std = ohlc[column].pct_change().rolling(window=period).std() * dev_factor
    upper_band = ma + std * ohlc[column]
    lower_band = ma - std * ohlc[column]
    return pd.DataFrame({"APZ_UPPER": upper_band, "APZ_LOWER": lower_band})

def VZO(ohlc,period = 14,column = "Close",colvol="Volume",adjust = True):
        """VZO uses price, previous price and moving averages to compute its oscillating value.
        It is a leading indicator that calculates buy and sell signals based on oversold / overbought conditions.
        Oscillations between the 5% and 40% levels mark a bullish trend zone, while oscillations between -40% and 5% mark a bearish trend zone.
        Meanwhile, readings above 40% signal an overbought condition, while readings above 60% signal an extremely overbought condition.
        Alternatively, readings below -40% indicate an oversold condition, which becomes extremely oversold below -60%."""

        sign = lambda a: (a > 0) - (a < 0)
        r = ohlc[column].diff().apply(sign) * ohlc[colvol]
        dvma = r.ewm(span=period, adjust=adjust).mean()
        vma = ohlc[colvol].ewm(span=period, adjust=adjust).mean()

        return pd.Series(100 * (dvma / vma), name="VZO")



def TR(ohlc,high="High",low="Low",close="Close"):
        """True Range is the maximum of three price ranges.
        Most recent period's high minus the most recent period's low.
        Absolute value of the most recent period's high minus the previous close.
        Absolute value of the most recent period's low minus the previous close."""

        TR1 = pd.Series(ohlc[high] - ohlc[low]).abs()  # True Range = High less Low

        TR2 = pd.Series(
            ohlc[high] - ohlc[close].shift()
        ).abs()  # True Range = High less Previous Close

        TR3 = pd.Series(
            ohlc[close].shift() - ohlc[low]
        ).abs()  # True Range = Previous Close less Low

        _TR = pd.concat([TR1, TR2, TR3], axis=1)

        _TR["TR"] = _TR.max(axis=1)

        return pd.Series(_TR["TR"], name="TR")

def ATR(ohlc, period = 14,high="High",low="Low",close="Close"):
        """Average True Range is moving average of True Range."""

        mytr=TR(ohlc,high=high,low=low,close=close)
        return pd.Series(
            mytr.rolling(center=False, window=period).mean(),
            name="{0} period ATR".format(period),
        )

def CHANDELIER(ohlc, short_period=22, long_period=22, k=3, high="High", low="Low"):
    """Chandelier Exit"""
    long_stop = ohlc[high].rolling(window=long_period).max() - ATR(ohlc, 22) * k
    short_stop = ohlc[low].rolling(window=short_period).min() + ATR(ohlc, 22) * k
    return pd.DataFrame({"CHANDELIER_Long": long_stop, "CHANDELIER_Short": short_stop})

def CE(ohlc, short_period=22, long_period=22, k=3, high="High", low="Low"):
    """Chandelier Exit"""
    long_stop = ohlc[high].rolling(window=long_period).max() - ATR(ohlc, 22) * k
    short_stop = ohlc[low].rolling(window=short_period).min() + ATR(ohlc, 22) * k
    return pd.DataFrame({"CHANDELIER_Long": long_stop, "CHANDELIER_Short": short_stop})

def BOP(ohlc,open="Open",column="Close",high="High",low="Low"):
    """Balance Of Power indicator"""

    return pd.Series(
        (ohlc[column] - ohlc[open]) / (ohlc[high] - ohlc[low]), name="BOP"
    )
    
    
def EV_MACD(ohlcv,period_fast = 20,period_slow = 40,signal = 9,adjust = True ):
        """
        Elastic Volume Weighted MACD is a variation of standard MACD,
        calculated using two EVWMA's.

        :period_slow: Specifies the number of Periods used for the slow EVWMA calculation
        :period_fast: Specifies the number of Periods used for the fast EVWMA calculation
        :signal: Specifies the number of Periods used for the signal calculation
        """

        evwma_slow = EVWMA(ohlcv, period_slow)

        evwma_fast = EVWMA(ohlcv, period_fast)

        MACD = pd.Series(evwma_fast - evwma_slow, name="MACD")
        MACD_signal = pd.Series(
            MACD.ewm(ignore_na=False, span=signal, adjust=adjust).mean(), name="SIGNAL"
        )

        return pd.concat([MACD, MACD_signal], axis=1)
    
def WILLIAMS(ohlc, period = 14,close="Close",high="High",low="Low"):
        """Williams %R, or just %R, is a technical analysis oscillator showing the current closing price in relation to the high and low
         of the past N days (for a given N). It was developed by a publisher and promoter of trading materials, Larry Williams.
         Its purpose is to tell whether a stock or commodity market is trading near the high or the low, or somewhere in between,
         of its recent trading range.
         The oscillator is on a negative scale, from −100 (lowest) up to 0 (highest).
        """

        highest_high = ohlc[high].rolling(center=False, window=period).max()
        lowest_low = ohlc[low].rolling(center=False, window=period).min()

        WR = pd.Series(
            (highest_high - ohlc[close]) / (highest_high - lowest_low),
            name="{0} Williams %R".format(period),
        )

        return WR * -100
    
def VORTEX(ohlc, period = 14,high="High",low="Low",column="Close"):
        """The Vortex indicator plots two oscillating lines, one to identify positive trend movement and the other
         to identify negative price movement.
         Indicator construction revolves around the highs and lows of the last two days or periods.
         The distance from the current high to the prior low designates positive trend movement while the
         distance between the current low and the prior high designates negative trend movement.
         Strongly positive or negative trend movements will show a longer length between the two numbers while
         weaker positive or negative trend movement will show a shorter length."""

        VMP = pd.Series((ohlc[high] - ohlc[low].shift()).abs())
        VMM = pd.Series((ohlc[low] - ohlc[high].shift()).abs())

        VMPx = VMP.rolling(window=period).sum()
        VMMx = VMM.rolling(window=period).sum()
        mytr = TR(ohlc,high=high,low=low,close=column).rolling(window=period).sum()

        VIp = pd.Series(VMPx / mytr, name="VIp").interpolate(method="index")
        VIm = pd.Series(VMMx / mytr, name="VIm").interpolate(method="index")

        return pd.concat([VIm, VIp], axis=1)
