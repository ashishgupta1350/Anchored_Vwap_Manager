1) Stop Loss Trailing
2) Live Anchored VWAP Chart (Logic to be determined)
3) Logic to not sell when crossing from above to below anchored vwap line
4) placing anchors on the "low" ? Idk
5) Buying only when down trend as confirmed by future's anchored vwap on same timeframe as the option ? 
6) Telegram signals for buy and sell
7) Telegram send chart of when buy / sell signal is generated


For charting, i can draw a chart and save as png in orders file. So , it displays open positions as blips and trades took in the past as blips too.



Head and shoulder pattern detection algorithm:
<img width="888" height="477" alt="image" src="https://github.com/user-attachments/assets/cfe50cff-03c4-4ba1-86e8-5a00eb358d39" />


ICICI Direct auto data fetcher API:

<img width="598" height="799" alt="image" src="https://github.com/user-attachments/assets/03f055dd-d6a4-4a84-8454-0583429e8dae" />

Auto Anchor Vwap using Local Minima Detection:
<img width="668" height="537" alt="image" src="https://github.com/user-attachments/assets/cfa6d374-bc41-4664-88b5-98cea1e6671a" />


Sell Signal Generations at occurance of anchored vwaps on local minimas:
<img width="536" height="535" alt="image" src="https://github.com/user-attachments/assets/954d3b27-0ae8-4b8c-b1b3-8b3db37e0254" />


Failed Signals:

<img width="591" height="549" alt="image" src="https://github.com/user-attachments/assets/72ea667c-67bb-4900-b72e-812f936d7abf" />

Successful Signals:

<img width="602" height="562" alt="image" src="https://github.com/user-attachments/assets/7f60a306-3aa7-40d9-b740-bae82ddb8491" />

Auto Signals lead to auto profits:

<img width="568" height="558" alt="image" src="https://github.com/user-attachments/assets/6779c1b0-f6f7-4bb6-95e2-446c92e05db5" />


Signal Logs generated as part of backtesting framework:

<img width="578" height="845" alt="image" src="https://github.com/user-attachments/assets/acf5db09-ab34-4d66-ba54-1769ac477e71" />


Note: The data can be found in Tester Part 1.ipynb and working of the code can be seen. This algorithm is inspired by AVWAP by Anirudh Singh and Myself Ashish Gupta 
