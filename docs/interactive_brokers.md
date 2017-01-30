##Interactive Brokers

###Account Types

* Cash
  Requires enough cash to cover transactions and commissions
* Margin
* Portfolio Margin
* IRA Margin

###Margin Accounts

* Margin
* Portfolio Margin
* IRA Margin

#####Securities Margin

* **Margin Loan**
  Amount of money that an investor borrows from his broker to buy securities.
* **Margin Deposit**
  Amount of equity contributed by the investor toward the purchase 
  of securities in a margin account.
* **Margin Requirement**
  The minimum amount that a customer must deposit and is commonly expressed
  as a percent of the current market value.

Margin Loan + Margin Deposit = Market Value of Security
Margin Deposit >= Margin Requirement

#####Securities Initial and Maintenance Margin

* **Initial Margin**
  'Regulation T' - up to 50 % borrow on security purchase
* **Maintenance Margin**
  At least 25 % of the total market value of the owned securities

#####Commodities Margin

An amount of equity contributed to support a futures contract.

Collateral = Amount of Equity Required to Support Futures Contract
Collateral >= Margin Requirement

Established by exchange through SPAN algorithm (Standard Portfolio Analysis of Risk)

#####Commodities Initial and Maintenance Margin

* Also Initial and Maintenance Margins
* Marked to Market daily, with account adjusted for any profit or loss that occurs.

###Universal Account

* Two underlying accounts:
    - Securities account (governed by the rules of SEC)
    - Futures account (governed by rules of CFTC (Commodity Futures Trading Commission))

#####Margin Model

* Rule-Based Margin System
  Predefined and static calculations applied to each position
  or predefined groups of positions ("strategies")
* Risk-Based Margin System
  Exchanges consider maximum one day risk on all the positions 
  in a complete portfolio, or sub-portfolio together.

| Account type      | Margin Calculations   | Products                                  |
|-------------------|-----------------------|-------------------------------------------|
| Margin            | Rule-Based            | US stocks, index options, stock options,  |
|                   |                       | single stock futures, and mutual funds    |
|                   |                       |                                           |
| All accounts      | Rule-Based            | Forex; Bonds; Canadian, European,         |
|                   |                       | and Asian stock; and Canadian stock       |
|                   |                       | options and index options                 |
|                   |                       |                                           |
| Portfolio Margin  | Risk-Based            | US stocks, index options, stock options,  |
|                   |                       | single stock futures, and mutual funds    |
|                   |                       |                                           |
| All accounts      | Risk-Based            | All futures and future options in any     |
|                   |                       | account. Non-US/Non-Canadian stock        |
|                   |                       | options and index options in any account. |
