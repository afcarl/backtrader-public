import datetime
import backtrader as bt
import backtrader.feeds as btfeed
import os



class maCross(bt.Strategy):

    def __init__(self):
        self.fast_ma = bt.ind.SMA(period=50)
        self.slow_ma = bt.ind.SMA(period=200)

        self.cross = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        self.orders = dict()
        for d in self.datas:
            self.orders[d.params.name] = None

    def stop(self):
        for d in self.datas:
            self.close(data=d)


    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def next(self):
        #print(self.orders)

        lot_dollars = self.broker.getvalue() / len(self.datas)*.9

        for i,d in enumerate(self.datas):
            security_name = d.params.name

            # we only allow one outstanding backet order per security. if this is not none, that means we have
            # a pending buy / stop loss / profit, so we continue
            # only needed for trailing stops without manual order cancellation
            #if self.orders[security_name] is not None:
            #    continue

            pos = self.getposition(d).size
            lot_size = int(lot_dollars / d.close[0])
            if self.cross[0] == 1:
                print("buying",lot_size)
                self.buy(data=d,size=lot_size)

                #trailing stop example
                #buy_order = self.buy(data=d,size=lot_size,transmit=False)
                #trail_stop = self.sell(data=d,size=lot_size,parent=buy_order,trailpercent=.015,exectype=bt.Order.StopTrail)
                #self.orders[security_name] = [buy_order,trail_stop]

                #bracket example
                #self.orders[security_name] = self.buy_bracket(data=d,size=lot_size,limitprice=d.close[0]*1.02,stopprice=d.close[0]*.98,exectype=bt.Order.Market)
            elif self.cross[0] == -1:
                print("selling",lot_size)
                self.sell(data=d,size=lot_size)
                #sell_order = self.sell(data=d,size=lot_size,transmit=False)
                #trail_stop = self.buy(data=d,size=lot_size,parent=sell_order,trailpercent=.015,exectype=bt.Order.StopTrail)
                #self.orders[security_name] = [sell_order,trail_stop]

                #self.orders[security_name] = self.buy_bracket(data=d,size=lot_size,limitprice=d.close[0]*.98,stopprice=d.close[0]*1.02,exectype=bt.Order.Market)



    def notify_order(self, order):

        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        security_name = order.params.data.params.name
        if order.status in [order.Completed]:
            if order.isbuy():
                pass
                self.log('BUY EXECUTED, %.6f' % order.executed.price)
            elif order.issell():
                pass
                self.log('SELL EXECUTED, %.6f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled]:
            self.log('Order Canceled')
        elif order.status in [order.Margin]:
            self.log('Order Margin')
        elif order.status in [order.Rejected]:
            self.log('Order Rejected')

        for k,v in self.orders.items():
            if v is None:
                continue
            for o in v:
                if not o.status in [o.Canceled,o.Margin,o.Rejected,o.Completed,]:
                    break
            else:
                self.orders[k] = None

class AcctValue(bt.Observer):
    alias = ('Value',)
    lines = ('value',)

    plotinfo = {"plot": True, "subplot": True}

    def next(self):
        self.lines.value[0] = self._owner.broker.getvalue() # Get today's account value (cash + stocks)

def add_data(cerebro):
    for txt in ['IBM.txt']:
        data = btfeed.GenericCSVData(dataname=txt,
                                     dtformat='%m/%d/%Y',
                                     #tmformat='%H:%M',
                                     name = os.path.splitext(txt)[0],

                                     fromdate=datetime.datetime(1990, 1, 1),
                                     todate=datetime.datetime(2019, 6, 1),

                                     #  nullvalue=0.0,

                                     datetime=0,
                                     #time=1,
                                     open=1,
                                     high=2,
                                     low=3,
                                     close=4,
                                     volume=5,
                                     openinterest=-6)
        cerebro.adddata(data)

cerebro = bt.Cerebro(stdstats=False)


cerebro.broker.set_cash(1000000) # Set our starting cash to $1,000,000
cerebro.addobserver(AcctValue)
add_data(cerebro)
cerebro.addstrategy(maCross)
cerebro.addobserver(bt.observers.DrawDown)

cerebro.run()
cerebro.plot()