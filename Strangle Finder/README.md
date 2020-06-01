This is a script that is used to find short strangles to trade upon by comparing the reward:risk ratio to the delta.

The idea is that if one consistently sells short strangles that are overvalued, then probability will make the person money.

The code is available in the Jupyter Notebook and the python file.

APIs used: tdameritrade with the TDA REST API, pandas, and a few other minor ones.

The following calculations had to be made in order to get this to work:
- Implied volatility of the equity. Uses NTM options values to estimate with a similar idea as with the VIX whitepaper.
- Standard deviation movement of the equity. Calculated using IV*equity_price*sqrt(days_to_exp/365). 252 may have also been used (or mentioned) as it is the number of trading days. I stayed more liberal (and matched how TDA calculates it) by using 365 days.
- Expected move of the stock. This is 2 std. devs. away from the current price (95% chance of being within that range). This is to calculate what the "managed" risk is (difference between expected move and strike price). Keep in mind that the theoretical risk of a short strangle is infinite.

To shorten the list of comparisons and test only options that I would actually trade, I have created a number of preconditions in find_strangle(). These include the liquidity of the equity, desirable deltas, OTM/ITM, and expiration dates.

I intend to use this as a pre-screener for good trades. I use this in conjunction with an Excel sheet that I created to manage my trades and evaluate my performance. I also do not blindly trade based upon the outcome of this script. Rather, I use it in conjunction with a number of other tools, a large number of which are available in Thinkorswim, and my own intuition.
- It's worth noting that my strategy is to enter only a couple trades every week. I am not doing any sort of day trading or high-frequency trading.

Also, I am not responsible for any usage of this software. I created this for fun. If anyone is interested in learning more about this and/or options/valuation/trading, feel free to reach out to me. I realize this isn't well documented (I don't expect anyone to ever actually see this), but if you have questions about it you can reach out to me and ask.


NASDAQ

https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nasdaq&render=download

AMEX

https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=amex&render=download

NYSE

https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nyse&render=download
