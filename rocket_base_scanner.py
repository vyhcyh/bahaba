#!/usr/bin/env python3
"""
Rocket Base Scanner - ALL 15 Original Conditions Strictly Enforced
This scanner implements the exact original 15 conditions without any relaxation
"""

import logging
import pandas as pd
import numpy as np
import yfinance as yf
import time
import os
from alpha_vantage.timeseries import TimeSeries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RocketBaseScanner:
    """Strict implementation of all 15 Rocket Base conditions"""
    
    def __init__(self):
        self.alpha_vantage_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
        if self.alpha_vantage_key:
            try:
                self.av_ts = TimeSeries(key=self.alpha_vantage_key, output_format='pandas')
                logger.info("Alpha Vantage initialized as backup")
            except Exception as e:
                logger.warning(f"Alpha Vantage initialization failed: {e}")
                self.alpha_vantage_key = None
        
        logger.info("Rocket Base Scanner initialized - ALL 15 CONDITIONS STRICTLY ENFORCED")
    
    def fetch_stock_data(self, symbol):
        """Fetch stock data with primary/backup sources"""
        try:
            # Try Yahoo Finance first (NSE)
            ticker = f"{symbol}.NS"
            stock = yf.Ticker(ticker)
            data = stock.history(period="90d")
            
            if data.empty:
                # Try BSE
                ticker = f"{symbol}.BO"
                stock = yf.Ticker(ticker)
                data = stock.history(period="90d")
            
            if not data.empty and len(data) >= 30:
                logger.info(f"Fetched {len(data)} days of Yahoo Finance data for {ticker}")
                return data, None
            
            # Try Alpha Vantage backup
            if self.alpha_vantage_key:
                try:
                    data, _ = self.av_ts.get_daily_adjusted(symbol=symbol, outputsize='compact')
                    if not data.empty and len(data) >= 30:
                        # Rename columns to match yfinance format
                        data = data.rename(columns={
                            '1. open': 'Open',
                            '2. high': 'High', 
                            '3. low': 'Low',
                            '4. close': 'Close',
                            '6. volume': 'Volume'
                        })
                        logger.info(f"Fetched {len(data)} days of Alpha Vantage data for {symbol}")
                        return data, None
                except Exception as e:
                    logger.warning(f"Alpha Vantage fetch failed for {symbol}: {e}")
            
            logger.warning(f"No data available for {symbol}")
            return None, "No data available"
            
        except Exception as e:
            logger.error(f"Data fetch error for {symbol}: {e}")
            return None, str(e)
    
    def calculate_technical_indicators(self, data):
        """Calculate all required technical indicators"""
        try:
            # WMA calculations
            data['WMA_1'] = data['Close']  # 1-period WMA = Close price
            data['WMA_2'] = self._wma(data['Close'], 2)
            data['WMA_4'] = self._wma(data['Close'], 4)
            data['WMA_6'] = self._wma(data['Close'], 6)
            data['WMA_12'] = self._wma(data['Close'], 12)
            data['WMA_20'] = self._wma(data['Close'], 20)
            
            # ATR and SMA
            data['ATR_5'] = self._atr(data, 5)
            data['SMA_ATR_5_10'] = self._sma(data['ATR_5'], 10)
            
            # RSI
            data['RSI_14'] = self._rsi(data['Close'], 14)
            
            return data
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return data
    
    def _wma(self, prices, period):
        """Weighted Moving Average calculation"""
        try:
            weights = np.arange(1, period + 1)
            return prices.rolling(window=period).apply(
                lambda x: np.dot(x, weights) / weights.sum() if len(x) == period else np.nan,
                raw=True
            )
        except:
            return pd.Series([np.nan] * len(prices), index=prices.index)
    
    def _sma(self, prices, period):
        """Simple Moving Average calculation"""
        try:
            return prices.rolling(window=period).mean()
        except:
            return pd.Series([np.nan] * len(prices), index=prices.index)
    
    def _atr(self, data, period):
        """Average True Range calculation"""
        try:
            high = data['High']
            low = data['Low']
            close = data['Close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            return true_range.rolling(window=period).mean()
        except:
            return pd.Series([np.nan] * len(data), index=data.index)
    
    def _rsi(self, prices, period):
        """Relative Strength Index calculation"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([np.nan] * len(prices), index=prices.index)
    
    def check_all_15_conditions(self, daily_data, weekly_data, monthly_data, symbol_data):
        """Check ALL 15 Rocket Base conditions STRICTLY"""
        try:
            # Get latest values
            latest = daily_data.iloc[-1]
            
            # ALL 15 CONDITIONS - STRICT ENFORCEMENT
            conditions = {}
            
            # PRE-FILTERS (Original conditions)
            # 1. Positive % Change Only - Excludes stocks with negative % change (≤ 0%)
            pct_change = symbol_data.get('pct_change')
            if pct_change is not None and pct_change <= 0:
                conditions['positive_change'] = False
                return None, conditions  # STRICT - Early exit for negative change
            else:
                conditions['positive_change'] = True
            
            # 2. No Major Corrections - Excludes stocks that corrected >20% in last 20 days
            if len(daily_data) >= 20:
                last_20_days = daily_data.tail(20)
                max_high = last_20_days['High'].max()
                current_close = latest['Close']
                correction = ((max_high - current_close) / max_high) * 100
                if correction > 20:
                    conditions['no_major_correction'] = False
                    return None, conditions  # STRICT - Early exit for major correction
                else:
                    conditions['no_major_correction'] = True
            else:
                conditions['no_major_correction'] = True
            
            # TECHNICAL ANALYSIS CONDITIONS (Original 13 conditions)
            try:
                # 3. Daily WMA(1) > Monthly WMA(2) + 1
                monthly_wma_2 = monthly_data['WMA_2'].iloc[-1] if not monthly_data.empty else np.nan
                conditions['daily_vs_monthly'] = (
                    not pd.isna(monthly_wma_2) and 
                    latest['WMA_1'] > (monthly_wma_2 + 1)
                )
                
                # 4. Monthly WMA(2) > Monthly WMA(4) + 2
                monthly_wma_4 = monthly_data['WMA_4'].iloc[-1] if not monthly_data.empty else np.nan
                conditions['monthly_momentum'] = (
                    not pd.isna(monthly_wma_2) and not pd.isna(monthly_wma_4) and
                    monthly_wma_2 > (monthly_wma_4 + 2)
                )
                
                # 5. Daily WMA(1) > Weekly WMA(6) + 2
                weekly_wma_6 = weekly_data['WMA_6'].iloc[-1] if not weekly_data.empty else np.nan
                conditions['daily_vs_weekly'] = (
                    not pd.isna(weekly_wma_6) and
                    latest['WMA_1'] > (weekly_wma_6 + 2)
                )
                
                # 6. Weekly WMA(6) > Weekly WMA(12) + 2
                weekly_wma_12 = weekly_data['WMA_12'].iloc[-1] if not weekly_data.empty else np.nan
                conditions['weekly_momentum'] = (
                    not pd.isna(weekly_wma_6) and not pd.isna(weekly_wma_12) and
                    weekly_wma_6 > (weekly_wma_12 + 2)
                )
                
                # 7. Daily WMA(1) > 4-day ago WMA(12) + 2
                if len(daily_data) >= 5:
                    wma_12_4_days_ago = daily_data['WMA_12'].iloc[-5]
                    conditions['historical_momentum_4d'] = (
                        not pd.isna(wma_12_4_days_ago) and
                        latest['WMA_1'] > (wma_12_4_days_ago + 2)
                    )
                else:
                    conditions['historical_momentum_4d'] = False
                
                # 8. Daily WMA(1) > 2-day ago WMA(20) + 2
                if len(daily_data) >= 3:
                    wma_20_2_days_ago = daily_data['WMA_20'].iloc[-3]
                    conditions['historical_momentum_2d'] = (
                        not pd.isna(wma_20_2_days_ago) and
                        latest['WMA_1'] > (wma_20_2_days_ago + 2)
                    )
                else:
                    conditions['historical_momentum_2d'] = False
                
                # 9. Daily Close > 25 and ≤ 500 (ORIGINAL STRICT RANGE)
                conditions['price_range'] = 25 < latest['Close'] <= 500
                
                # 10. Weekly Volume > 85,000 (ORIGINAL STRICT THRESHOLD)
                weekly_volume = weekly_data['Volume'].iloc[-1] if not weekly_data.empty else 0
                conditions['volume_threshold'] = weekly_volume > 85000
                
                # 11. ATR(5) < SMA(ATR(5),10) - Volatility compression
                conditions['atr_compression'] = (
                    not pd.isna(latest['ATR_5']) and not pd.isna(latest['SMA_ATR_5_10']) and
                    latest['ATR_5'] < latest['SMA_ATR_5_10']
                )
                
                # 12. 5-day price range < 10% - Recent stability check
                if len(daily_data) >= 5:
                    last_5_days = daily_data.tail(5)
                    high_5d = last_5_days['High'].max()
                    low_5d = last_5_days['Low'].min()
                    price_range_5d = ((high_5d - low_5d) / low_5d) * 100
                    conditions['price_stability'] = price_range_5d < 10
                else:
                    conditions['price_stability'] = False
                
                # 13. RSI(14) > 60 (ORIGINAL STRICT THRESHOLD)
                conditions['rsi_strength'] = (
                    not pd.isna(latest['RSI_14']) and latest['RSI_14'] > 60
                )
                
                # 14. Volume Contraction During Base: AvgVolume_5 < AvgVolume_10
                if len(daily_data) >= 10:
                    avg_vol_5 = daily_data['Volume'].tail(5).mean()
                    avg_vol_10 = daily_data['Volume'].tail(10).mean()
                    conditions['volume_contraction'] = avg_vol_5 < avg_vol_10
                else:
                    conditions['volume_contraction'] = False
                
                # 15. Last 5 Days % Change Filter: Exclude stocks with >8% change in last 5 days
                last_5day_change = symbol_data.get('last_5day_change')
                if last_5day_change is not None and abs(last_5day_change) > 8:
                    conditions['last_5day_change'] = False
                else:
                    conditions['last_5day_change'] = True
                
                # STRICT ENFORCEMENT: ALL CONDITIONS MUST PASS
                all_passed = all(conditions.values())
                
                if all_passed:
                    result = {
                        'symbol': symbol_data['symbol'],
                        'current_price': float(latest['Close']),
                        'rsi': float(latest['RSI_14']) if not pd.isna(latest['RSI_14']) else None,
                        'volume': float(latest['Volume']),
                        'conditions_met': len([c for c in conditions.values() if c]),
                        'total_conditions': len(conditions),
                        'conditions_detail': conditions,
                        'pct_change': symbol_data.get('pct_change')
                    }
                    return result, conditions
                
                return None, conditions
                
            except Exception as e:
                logger.error(f"Error checking technical conditions: {e}")
                return None, {}
                
        except Exception as e:
            logger.error(f"Error in check_all_15_conditions: {e}")
            return None, {}
    
    def scan_single_stock(self, symbol, symbol_data):
        """Scan single stock with ALL 15 strict conditions"""
        try:
            logger.info(f"Scanning {symbol} - ALL 15 CONDITIONS REQUIRED")
            
            # Fetch data
            daily_data, error = self.fetch_stock_data(symbol)
            if daily_data is None:
                return None
            
            # Calculate indicators
            daily_data = self.calculate_technical_indicators(daily_data)
            
            # Create weekly and monthly data
            weekly_data = daily_data.resample('W').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
            
            monthly_data = daily_data.resample('ME').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
            
            # Calculate weekly and monthly WMAs
            if len(weekly_data) >= 12:
                weekly_data['WMA_6'] = self._wma(weekly_data['Close'], 6)
                weekly_data['WMA_12'] = self._wma(weekly_data['Close'], 12)
            
            if len(monthly_data) >= 4:
                monthly_data['WMA_2'] = self._wma(monthly_data['Close'], 2)
                monthly_data['WMA_4'] = self._wma(monthly_data['Close'], 4)
            
            # Check ALL 15 conditions STRICTLY
            result, conditions = self.check_all_15_conditions(daily_data, weekly_data, monthly_data, symbol_data)
            
            if result:
                logger.info(f"✓ {symbol} PASSED ALL 15 CONDITIONS!")
                return result
            else:
                passed = sum(conditions.values()) if conditions else 0
                logger.info(f"✗ {symbol} failed - {passed}/15 conditions")
                return None
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            return None

if __name__ == "__main__":
    # Test the strict scanner
    scanner = RocketBaseScanner()
    test_symbols = [
        {'symbol': 'GMDCLTD', 'name': 'Gujarat Mineral Development Corporation', 'pct_change': 14.73, 'last_5day_change': None},
        {'symbol': 'RELIANCE', 'name': 'Reliance Industries', 'pct_change': 1.2, 'last_5day_change': 3.5}
    ]
    
    for symbol_data in test_symbols:
        result = scanner.scan_single_stock(symbol_data['symbol'], symbol_data)
        if result:
            print(f"PASSED ALL 15: {symbol_data['symbol']}")
        else:
            print(f"FAILED: {symbol_data['symbol']}")