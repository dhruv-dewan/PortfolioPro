from snaptrade_client import SnapTrade
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import SecretStr

class User:
    def __init__(self, userId: str, userSecret: str, brokerage_accounts: dict = None) -> None:
        """Initialize a User with SnapTrade credentials.
        
        Args:
            userId: SnapTrade user ID
            userSecret: SnapTrade user secret
            brokerage_accounts: Optional dictionary mapping accountId to brokerage account data
        """
        self.userId = userId
        self.userSecret = SecretStr(userSecret)
        self.brokerage_accounts = brokerage_accounts if brokerage_accounts is not None else {}
        self.holdings: Dict[str, dict] = {}  # Store holdings snapshots by account_name
        
    def pull_connected_brokerage_accounts(self, snaptrade_client: SnapTrade) -> bool:
        """Pull connected brokerage accounts for the user and update the hashtable.
        
        This function should retrieve all brokerage accounts associated with the user
        and store them in the brokerage_accounts dictionary with institution_name as keys and account_id as values.
        """
        try:
            accounts = snaptrade_client.account_information.list_user_accounts(
                user_id=self.userId,
                user_secret=self.userSecret.get_secret_value()
            )
            for account in accounts.body:
                self.brokerage_accounts[account["name"]] = account["id"]
            return True
        except Exception as e:
            print(f"Error pulling connected brokerage accounts: {e}")
            return False
        
    def pull_account_holdings(self, snaptrade_client: SnapTrade, account_name: str) -> bool:
        """Pull holdings for a given account and create a clean snapshot.
        
        Args:
            snaptrade_client: SnapTrade client instance
            account_name: Name of the account to pull holdings for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            holdings_data = snaptrade_client.account_information.get_user_holdings(
                account_id=self.brokerage_accounts[account_name],
                user_id=self.userId,
                user_secret=self.userSecret.get_secret_value()
            )
            
            # Create clean snapshot structure
            snapshot = self._create_holdings_snapshot(holdings_data.body)
            self.holdings[account_name] = snapshot
            return True
            
        except Exception as e:
            print(f"Error pulling holdings for {account_name}: {e}")
            return False
    
    def _create_holdings_snapshot(self, holdings_data: dict) -> dict:
        """Create a clean, structured holdings snapshot for AI analysis.
        
        Args:
            holdings_data: Raw holdings data from SnapTrade API
            
        Returns:
            dict: Clean snapshot structure
        """
        snapshot = {
            # 1. Snapshot Metadata (Critical)
            "metadata": {
                "account_id": holdings_data.get("account", {}).get("id"),
                "account_name": holdings_data.get("account", {}).get("name"),
                "pulled_at": datetime.now().isoformat(),
                "institution_name": holdings_data.get("account", {}).get("institution_name")
            },
            
            # 2. Account Balances (Critical for Portfolio Tracking)
            "balances": {
                "total_balance": holdings_data.get("account", {}).get("balance", {}).get("total", {}).get("amount"),
                "total_balance_currency": holdings_data.get("account", {}).get("balance", {}).get("total", {}).get("currency"),
                "cash_available": holdings_data.get("balances", [{}])[0].get("cash") if holdings_data.get("balances") else None,
                "buying_power": holdings_data.get("balances", [{}])[0].get("buying_power") if holdings_data.get("balances") else None,
                "total_portfolio_value": holdings_data.get("total_value", {}).get("value"),
                "total_portfolio_currency": holdings_data.get("total_value", {}).get("currency")
            },
            
            # 3. Positions (Critical for Portfolio Analytics)
            "positions": []
        }
        
        # Process regular positions
        for position in holdings_data.get("positions", []):
            position_data = {
                "symbol": position.get("symbol", {}).get("symbol", {}).get("symbol"),
                "description": position.get("symbol", {}).get("description"),
                "units": position.get("units"),
                "fractional_units": position.get("fractional_units"),
                "current_price": position.get("price"),
                "average_purchase_price": position.get("average_purchase_price"),
                "open_pnl": position.get("open_pnl"),
                "exchange": position.get("symbol", {}).get("symbol", {}).get("exchange", {}).get("code"),
                "asset_type": position.get("symbol", {}).get("symbol", {}).get("type", {}).get("description"),
                "currency": position.get("symbol", {}).get("symbol", {}).get("currency", {}).get("code")
            }
            snapshot["positions"].append(position_data)
        
        # 4. Option Positions (Critical for Risk & Strategy Insights)
        snapshot["option_positions"] = []
        for option in holdings_data.get("option_positions", []):
            option_data = {
                "underlying_symbol": option.get("symbol", {}).get("option_symbol", {}).get("underlying_symbol", {}).get("symbol"),
                "option_ticker": option.get("symbol", {}).get("option_symbol", {}).get("ticker"),
                "option_type": option.get("symbol", {}).get("option_symbol", {}).get("option_type"),
                "strike_price": option.get("symbol", {}).get("option_symbol", {}).get("strike_price"),
                "expiration_date": option.get("symbol", {}).get("option_symbol", {}).get("expiration_date"),
                "units": option.get("units"),
                "current_price": option.get("price"),
                "average_purchase_price": option.get("average_purchase_price"),
                "currency": option.get("currency", {}).get("code")
            }
            snapshot["option_positions"].append(option_data)
        
        # 5. Orders (Important for Transaction History & Insights)
        snapshot["orders"] = []
        for order in holdings_data.get("orders", []):
            order_data = {
                "brokerage_order_id": order.get("brokerage_order_id"),
                "symbol": order.get("universal_symbol", {}).get("symbol"),
                "action": order.get("action"),
                "total_quantity": order.get("total_quantity"),
                "filled_quantity": order.get("filled_quantity"),
                "execution_price": order.get("execution_price"),
                "order_type": order.get("order_type"),
                "limit_price": order.get("limit_price"),
                "stop_price": order.get("stop_price"),
                "status": order.get("status"),
                "time_placed": order.get("time_placed"),
                "time_executed": order.get("time_executed"),
                "time_updated": order.get("time_updated"),
                "expiry_date": order.get("expiry_date")
            }
            
            # Add option-specific fields if applicable
            if order.get("option_symbol"):
                order_data["option_symbol"] = {
                    "ticker": order.get("option_symbol", {}).get("ticker"),
                    "option_type": order.get("option_symbol", {}).get("option_type"),
                    "strike_price": order.get("option_symbol", {}).get("strike_price"),
                    "expiration_date": order.get("option_symbol", {}).get("expiration_date")
                }
            
            snapshot["orders"].append(order_data)
        
        return snapshot
        
    def small_holdings_snapshot(self, account_name: str) -> dict:
        """Create a small, structured holdings snapshot for AI analysis.
        
        Note: This simplified snapshot does not include option positions as of now.
        
        Args:
            account_name: Name of the account to get snapshot for
            
        Returns:
            dict: Small snapshot structure with essential data only
        """
        if account_name not in self.holdings:
            return {}
            
        holdings_data = self.holdings[account_name]
        
        snapshot = {
            "snapshot_date": holdings_data.get("metadata", {}).get("pulled_at"),
            "account": holdings_data.get("metadata", {}).get("account_name"),
            "balances": {
                "total_balance": holdings_data.get("balances", {}).get("total_balance"),
                "cash_available": holdings_data.get("balances", {}).get("cash_available"),
                "buying_power": holdings_data.get("balances", {}).get("buying_power"),
                "total_portfolio_value": holdings_data.get("balances", {}).get("total_portfolio_value")
            },
            "positions": []
        }
        
        # Extract only essential position data
        for position in holdings_data.get("positions", []):
            position_data = {
                "symbol": position.get("symbol"),
                "units": position.get("units"),
                "current_price": position.get("current_price"),
                "open_pnl": position.get("open_pnl")
            }
            snapshot["positions"].append(position_data)
        
        return snapshot

    def format_portfolio_summary(self, account_name: str) -> str:
        """Format the small holdings snapshot into a clean, readable portfolio summary.
        
        Args:
            account_name: Name of the account to format summary for
            
        Returns:
            str: Formatted portfolio summary text
        """
        snapshot = self.small_holdings_snapshot(account_name)
        
        if not snapshot:
            return f"No holdings data available for account: {account_name}"
        
        # Format the summary
        summary = []
        summary.append("=" * 50)
        summary.append(f"PORTFOLIO SUMMARY - {snapshot['account']}")
        summary.append("=" * 50)
        summary.append(f"Snapshot Date: {snapshot['snapshot_date']}")
        summary.append("")
        
        # Account Balances
        balances = snapshot['balances']
        summary.append("📊 ACCOUNT BALANCES")
        summary.append("-" * 20)
        summary.append(f"Total Balance: ${balances['total_balance']:,.2f}")
        summary.append(f"Cash Available: ${balances['cash_available']:,.2f}")
        summary.append(f"Buying Power: ${balances['buying_power']:,.2f}")
        if balances.get('total_portfolio_value'):
            summary.append(f"Portfolio Value: ${balances['total_portfolio_value']:,.2f}")
        summary.append("")
        
        # Positions
        positions = snapshot['positions']
        if positions:
            summary.append("📈 POSITIONS")
            summary.append("-" * 20)
            
            # Calculate total portfolio value from positions
            total_position_value = sum(pos['units'] * pos['current_price'] for pos in positions)
            total_pnl = sum(pos['open_pnl'] for pos in positions)
            
            for position in positions:
                symbol = position['symbol']
                units = position['units']
                current_price = position['current_price']
                open_pnl = position['open_pnl']
                position_value = units * current_price
                
                # Format PnL with color indicators
                pnl_sign = "+" if open_pnl >= 0 else ""
                pnl_indicator = "🟢" if open_pnl >= 0 else "🔴"
                
                summary.append(f"{symbol}:")
                summary.append(f"  Units: {units:,.4f}")
                summary.append(f"  Current Price: ${current_price:.2f}")
                summary.append(f"  Position Value: ${position_value:,.2f}")
                summary.append(f"  P&L: {pnl_indicator} {pnl_sign}${open_pnl:.2f}")
                summary.append("")
            
            # Portfolio summary
            summary.append("📋 PORTFOLIO SUMMARY")
            summary.append("-" * 20)
            summary.append(f"Total Positions Value: ${total_position_value:,.2f}")
            summary.append(f"Total P&L: {'+' if total_pnl >= 0 else ''}${total_pnl:.2f}")
            
            # Calculate percentage gain/loss if we have portfolio value
            if balances.get('total_portfolio_value') and total_position_value > 0:
                pnl_percentage = (total_pnl / total_position_value) * 100
                summary.append(f"P&L %: {'+' if pnl_percentage >= 0 else ''}{pnl_percentage:.2f}%")
        else:
            summary.append("📈 POSITIONS")
            summary.append("-" * 20)
            summary.append("No positions found")
        
        summary.append("")
        summary.append("=" * 50)
        
        return "\n".join(summary)
