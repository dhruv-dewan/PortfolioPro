from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import json

def localInsights(small_snapshot) -> str:
    """
    Generate portfolio insights using local Ollama model.
    
    Args:
        small_snapshot: Portfolio snapshot from User.small_holdings_snapshot()
        
    Returns:
        str: Formatted insights about the portfolio
    """
    model = ChatOllama(model="deepseek-r1")

    # Format the snapshot as a readable string for the model
    formatted_snapshot = _format_snapshot_for_llm(small_snapshot)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert financial analyst specializing in portfolio analysis and investment insights. 
        
Your task is to analyze a user's investment portfolio snapshot and provide actionable insights. Focus on:

1. **Portfolio Overview**: Summarize the current state and key metrics
2. **Risk Assessment**: Evaluate diversification, concentration, and potential risks
3. **Performance Analysis**: Analyze P&L patterns and position performance
4. **Actionable Recommendations**: Provide specific, actionable advice
5. **Market Context**: Consider current market conditions in your analysis

Be concise but comprehensive. Use bullet points for clarity. If you notice any concerning patterns or opportunities, highlight them prominently.

Format your response with clear sections and use emojis sparingly for visual organization. Do not overwhelm the user, but do not be too brief. Be concise and to the point."""),
        ("user", f"Please analyze this portfolio snapshot and provide insights:\n\n{formatted_snapshot}")
    ])

    chain = prompt | model
    response = chain.invoke({"small_snapshot": formatted_snapshot})
    
    return response.content

def _format_snapshot_for_llm(snapshot: dict) -> str:
    """
    Format the small snapshot into a clear, structured text for LLM consumption.
    
    Args:
        snapshot: Small holdings snapshot dictionary
        
    Returns:
        str: Formatted snapshot text
    """
    if not snapshot:
        return "No portfolio data available for analysis."
    
    formatted = []
    formatted.append(f"PORTFOLIO SNAPSHOT")
    formatted.append(f"Account: {snapshot.get('account', 'Unknown')}")
    formatted.append(f"Date: {snapshot.get('snapshot_date', 'Unknown')}")
    formatted.append("")
    
    # Balances
    balances = snapshot.get('balances', {})
    formatted.append("ACCOUNT BALANCES:")
    formatted.append(f"  Total Balance: ${balances.get('total_balance', 0):,.2f}")
    formatted.append(f"  Cash Available: ${balances.get('cash_available', 0):,.2f}")
    formatted.append(f"  Buying Power: ${balances.get('buying_power', 0):,.2f}")
    if balances.get('total_portfolio_value'):
        formatted.append(f"  Portfolio Value: ${balances.get('total_portfolio_value'):,.2f}")
    formatted.append("")
    
    # Positions
    positions = snapshot.get('positions', [])
    if positions:
        formatted.append("POSITIONS:")
        total_position_value = 0
        total_pnl = 0
        
        for position in positions:
            symbol = position.get('symbol', 'Unknown')
            units = position.get('units', 0)
            current_price = position.get('current_price', 0)
            open_pnl = position.get('open_pnl', 0)
            position_value = units * current_price
            
            total_position_value += position_value
            total_pnl += open_pnl
            
            formatted.append(f"  {symbol}:")
            formatted.append(f"    Units: {units:,.4f}")
            formatted.append(f"    Current Price: ${current_price:.2f}")
            formatted.append(f"    Position Value: ${position_value:,.2f}")
            formatted.append(f"    P&L: {'+' if open_pnl >= 0 else ''}${open_pnl:.2f}")
            formatted.append("")
        
        # Portfolio summary
        formatted.append("PORTFOLIO SUMMARY:")
        formatted.append(f"  Total Positions Value: ${total_position_value:,.2f}")
        formatted.append(f"  Total P&L: {'+' if total_pnl >= 0 else ''}${total_pnl:.2f}")
        
        if total_position_value > 0:
            pnl_percentage = (total_pnl / total_position_value) * 100
            formatted.append(f"  P&L %: {'+' if pnl_percentage >= 0 else ''}{pnl_percentage:.2f}%")
    else:
        formatted.append("POSITIONS: No positions found")
    
    return "\n".join(formatted)