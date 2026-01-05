"""Multi-Chain Real-Time Token Detector - AMÉLIORÉ avec tous les liens"""
import asyncio
import logging
from web3 import Web3
from web3.exceptions import BlockNotFound
from typing import List, Dict
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ABIs
UNISWAP_V2_FACTORY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "token0", "type": "address"},
            {"indexed": True, "name": "token1", "type": "address"},
            {"indexed": False, "name": "pair", "type": "address"},
            {"indexed": False, "name": "", "type": "uint256"}
        ],
        "name": "PairCreated",
        "type": "event"
    }
]

ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "owner", "outputs": [{"name": "", "type": "address"}], "type": "function"}
]

PAIR_ABI = [
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [
        {"name": "reserve0", "type": "uint112"},
        {"name": "reserve1", "type": "uint112"},
        {"name": "blockTimestampLast", "type": "uint32"}
    ], "type": "function"},
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"}
]

# Configuration des DEX par blockchain
DEX_FACTORIES = {
    "ETH": {
        "uniswap_v2": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        "sushiswap": "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"
    },
    "BSC": {
        "pancakeswap_v2": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73",
        "biswap": "0x858E3312ed3A876947EA49d572A7C42DE08af7EE"
    }
}

WRAPPED_NATIVE = {
    "ETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "BSC": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
}

# Prix estimés (idéalement à remplacer par API)
NATIVE_PRICES = {
    "ETH": 2300,
    "BSC": 320
}


class MultiChainDetector:
    def __init__(self, chains: List[str], rpc_manager, config: dict):
        self.chains = chains
        self.rpc_manager = rpc_manager
        self.config = config
        self.event_queue = asyncio.Queue()
        self.running = False
        self.web3_connections = {}
        self.last_scanned_blocks = {}
        self.detected_tokens = set()
        self.min_liquidity_usd = config.get("MIN_LIQUIDITY_USD", 5000)
        self.scan_interval = config.get("SCAN_INTERVAL_SECONDS", 3)
        self.connection_errors = {}
        self.total_detections = 0
        
    def _get_web3(self, chain: str) -> Web3:
        if chain not in self.web3_connections:
            rpc_url = self.rpc_manager.get(chain)
            if not rpc_url:
                raise ValueError(f"No RPC URL for chain {chain}")
            
            logger.info(f"🔗 Connecting to {chain} RPC: {rpc_url}")
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 60}))
            
            try:
                block = w3.eth.block_number
                logger.info(f"✅ Connected to {chain} - Current block: {block}")
                self.web3_connections[chain] = w3
            except Exception as e:
                logger.error(f"❌ Failed to connect to {chain}: {e}")
                raise
        
        return self.web3_connections[chain]
    
    async def start(self):
        self.running = True
        logger.info(f"🚀 Starting detector for chains: {self.chains}")
        
        tasks = []
        for chain in self.chains:
            try:
                self._get_web3(chain)
                tasks.append(asyncio.create_task(self._scan_blocks(chain)))
            except Exception as e:
                logger.error(f"❌ Cannot start detector for {chain}: {e}")
                self.connection_errors[chain] = str(e)
        
        if not tasks:
            logger.error("❌ No valid RPC connections - detector cannot start")
            self.running = False
            return
        
        tasks.append(asyncio.create_task(self._print_stats()))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        self.running = False
        logger.info("🛑 Stopping detector...")
    
    async def _scan_blocks(self, chain: str):
        try:
            w3 = self._get_web3(chain)
            current_block = w3.eth.block_number
            self.last_scanned_blocks[chain] = current_block
            
            logger.info(f"📡 Started block scanner for {chain} at block {current_block}")
            
            consecutive_errors = 0
            
            while self.running:
                try:
                    current_block = w3.eth.block_number
                    last_block = self.last_scanned_blocks.get(chain, current_block - 1)
                    
                    if current_block > last_block:
                        logger.debug(f"📊 {chain} - Scanning blocks {last_block + 1} to {current_block}")
                        
                        for block_num in range(last_block + 1, min(last_block + 10, current_block + 1)):
                            await self._scan_block_for_pairs(chain, block_num, w3)
                        
                        self.last_scanned_blocks[chain] = current_block
                        consecutive_errors = 0
                    
                    await asyncio.sleep(self.scan_interval)
                    
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"❌ Block scan error for {chain} (attempt {consecutive_errors}): {e}")
                    
                    if consecutive_errors >= 5:
                        logger.critical(f"❌ Too many errors for {chain} - stopping scanner")
                        self.connection_errors[chain] = f"Stopped after {consecutive_errors} errors"
                        break
                    
                    await asyncio.sleep(10)
        
        except Exception as e:
            logger.critical(f"❌ Fatal error in {chain} scanner: {e}")
            self.connection_errors[chain] = str(e)
    
    async def _scan_block_for_pairs(self, chain: str, block_number: int, w3: Web3):
        try:
            factories = DEX_FACTORIES.get(chain, {})
            
            for dex_name, factory_address in factories.items():
                factory_contract = w3.eth.contract(
                    address=Web3.to_checksum_address(factory_address),
                    abi=UNISWAP_V2_FACTORY_ABI
                )
                
                events = factory_contract.events.PairCreated.get_logs(
                    fromBlock=block_number,
                    toBlock=block_number
                )
                
                for event in events:
                    await self._process_pair_created(chain, dex_name, event, w3)
                    
        except BlockNotFound:
            pass
        except Exception as e:
            logger.debug(f"Scan block {block_number} on {chain}: {e}")
    
    async def _process_pair_created(self, chain: str, dex: str, event, w3: Web3):
        try:
            token0 = event['args']['token0']
            token1 = event['args']['token1']
            pair_address = event['args']['pair']
            
            wrapped_native = WRAPPED_NATIVE.get(chain)
            
            new_token = None
            if token0.lower() == wrapped_native.lower():
                new_token = token1
            elif token1.lower() == wrapped_native.lower():
                new_token = token0
            else:
                return
            
            token_id = f"{chain}:{new_token.lower()}"
            if token_id in self.detected_tokens:
                return
            
            self.detected_tokens.add(token_id)
            
            # Récupérer TOUTES les infos + GÉNÉRER TOUS LES LIENS
            token_info = await self._get_complete_token_info(chain, new_token, pair_address, dex, w3)
            
            if not await self._should_analyze(token_info):
                logger.info(f"⏭️ Token filtered: {token_info.get('symbol', '???')} - Liquidity: ${token_info.get('liquidity_usd', 0):,.0f}")
                return
            
            # Générer TOUS les liens directs
            links = self._generate_all_links(chain, new_token, pair_address)
            
            detection_event = {
                "chain": chain,
                "dex": dex,
                "token_address": new_token,
                "pair_address": pair_address,
                "block_number": event['blockNumber'],
                "timestamp": datetime.utcnow().isoformat(),
                "detection_time": time.time(),
                "links": links,  # ← NOUVEAU : Tous les liens
                **token_info
            }
            
            self.total_detections += 1
            await self.event_queue.put(detection_event)
            
            # Affichage complet
            self._print_detection_with_links(detection_event)
            
        except Exception as e:
            logger.error(f"Error processing PairCreated: {e}")
    
    def _generate_all_links(self, chain: str, token_address: str, pair_address: str) -> Dict:
        """Génère TOUS les liens utiles pour le token"""
        links = {}
        
        if chain == "ETH":
            links = {
                # Explorateurs
                "etherscan_token": f"https://etherscan.io/token/{token_address}",
                "etherscan_pair": f"https://etherscan.io/address/{pair_address}",
                
                # DEX
                "uniswap": f"https://app.uniswap.org/#/swap?outputCurrency={token_address}",
                
                # Charts
                "dextools": f"https://www.dextools.io/app/ether/pair-explorer/{pair_address}",
                "dexscreener": f"https://dexscreener.com/ethereum/{pair_address}",
                "poocoin": f"https://poocoin.app/tokens/eth/{token_address}",
                "ave_tools": f"https://ave.ai/token/{token_address}-eth",
                
                # Sécurité
                "honeypot_is": f"https://honeypot.is/ethereum?address={token_address}",
                "tokensniffer": f"https://tokensniffer.com/token/eth/{token_address}",
            }
        
        elif chain == "BSC":
            links = {
                # Explorateurs
                "bscscan_token": f"https://bscscan.com/token/{token_address}",
                "bscscan_pair": f"https://bscscan.com/address/{pair_address}",
                
                # DEX
                "pancakeswap": f"https://pancakeswap.finance/swap?outputCurrency={token_address}",
                
                # Charts
                "dextools": f"https://www.dextools.io/app/bnb/pair-explorer/{pair_address}",
                "dexscreener": f"https://dexscreener.com/bsc/{pair_address}",
                "poocoin": f"https://poocoin.app/tokens/{token_address}",
                "ave_tools": f"https://ave.ai/token/{token_address}-bsc",
                
                # Sécurité
                "honeypot_is": f"https://honeypot.is/bsc?address={token_address}",
                "tokensniffer": f"https://tokensniffer.com/token/bsc/{token_address}",
                "rugcheck": f"https://rugcheck.xyz/tokens/{token_address}",
            }
        
        return links
    
    def _print_detection_with_links(self, d: dict):
        """Affichage avec TOUS les liens"""
        
        BOLD = '\033[1m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        RED = '\033[91m'
        RESET = '\033[0m'
        
        print("\n" + "="*120)
        print(f"{BOLD}{GREEN}🎯 NOUVEAU TOKEN DÉTECTÉ #{self.total_detections}{RESET}")
        print("="*120)
        
        # Identification
        print(f"\n{BOLD}{CYAN}📌 IDENTIFICATION{RESET}")
        print(f"  Chain: {BOLD}{d['chain']}{RESET}")
        print(f"  DEX: {BOLD}{d['dex']}{RESET}")
        print(f"  Name: {BOLD}{d.get('name', 'N/A')}{RESET}")
        print(f"  Symbol: {BOLD}{d.get('symbol', 'N/A')}{RESET} (${d.get('symbol', '')})")
        print(f"  Detection: {d['timestamp']}")
        
        # Adresses
        print(f"\n{BOLD}{CYAN}🔗 SMART CONTRACTS{RESET}")
        print(f"  Token: {BOLD}{d['token_address']}{RESET}")
        print(f"  Pair: {d['pair_address']}")
        print(f"  Owner: {d.get('owner_address', 'N/A')}")
        
        # Supply
        print(f"\n{BOLD}{CYAN}💰 SUPPLY{RESET}")
        print(f"  Total: {BOLD}{d.get('total_supply_formatted', 'N/A')}{RESET} {d.get('symbol', '')}")
        if d.get('owner_balance_percent', 0) > 0:
            color = RED if d['owner_balance_percent'] > 20 else YELLOW if d['owner_balance_percent'] > 10 else GREEN
            print(f"  Owner: {color}{d['owner_balance_percent']:.2f}%{RESET}")
        
        # Liquidité
        print(f"\n{BOLD}{CYAN}💎 LIQUIDITÉ{RESET}")
        print(f"  Reserve: {BOLD}{d.get('liquidity_native', 0):.4f} {d.get('native_token', 'ETH')}{RESET}")
        
        liq_color = GREEN if d.get('liquidity_usd', 0) > 50000 else YELLOW if d.get('liquidity_usd', 0) > 20000 else RED
        print(f"  USD: {liq_color}${d.get('liquidity_usd', 0):,.2f}{RESET}")
        
        # Prix
        print(f"\n{BOLD}{CYAN}📈 PRIX & MARKET CAP{RESET}")
        print(f"  Price: {BOLD}${d.get('price_usd', 0):.10f}{RESET}")
        print(f"  Market Cap: ${d.get('market_cap_usd', 0):,.2f}")
        
        # Sécurité
        print(f"\n{BOLD}{CYAN}🔒 SÉCURITÉ{RESET}")
        print(f"  Ownership: {GREEN}✓ Renounced{RESET}" if d.get('ownership_renounced') else f"  Ownership: {RED}✗ Not Renounced{RESET}")
        
        if d.get('has_mint_function'):
            print(f"  {RED}⚠ Mint Function{RESET}")
        if d.get('has_pause_function'):
            print(f"  {YELLOW}⚠ Pause Function{RESET}")
        if d.get('has_blacklist'):
            print(f"  {RED}⚠ Blacklist{RESET}")
        if d.get('has_proxy'):
            print(f"  {RED}⚠ Proxy Pattern{RESET}")
        
        if not any([d.get('has_mint_function'), d.get('has_pause_function'), d.get('has_blacklist'), d.get('has_proxy')]):
            print(f"  {GREEN}✓ No dangerous functions{RESET}")
        
        # Score de risque
        risk = d.get('risk_score', 50)
        if risk < 30:
            print(f"\n{BOLD}{CYAN}⚡ RISQUE: {GREEN}LOW ({risk}/100) ✅{RESET}")
        elif risk < 60:
            print(f"\n{BOLD}{CYAN}⚡ RISQUE: {YELLOW}MEDIUM ({risk}/100) ⚠️{RESET}")
        else:
            print(f"\n{BOLD}{CYAN}⚡ RISQUE: {RED}HIGH ({risk}/100) 🚨{RESET}")
        
        # === SECTION LIENS (LE PLUS IMPORTANT) ===
        print(f"\n{BOLD}{CYAN}🔍 LIENS DIRECTS - CLIQUEZ POUR ANALYSER{RESET}")
        print(f"{BOLD}{BLUE}{'─'*116}{RESET}")
        
        links = d.get('links', {})
        
        if d['chain'] == 'ETH':
            print(f"\n  {BOLD}📊 EXPLORATEURS:{RESET}")
            print(f"     Etherscan Token: {BLUE}{links.get('etherscan_token', 'N/A')}{RESET}")
            print(f"     Etherscan Pair:  {BLUE}{links.get('etherscan_pair', 'N/A')}{RESET}")
            
            print(f"\n  {BOLD}💱 DEX & TRADING:{RESET}")
            print(f"     Uniswap: {BLUE}{links.get('uniswap', 'N/A')}{RESET}")
            
            print(f"\n  {BOLD}📈 CHARTS:{RESET}")
            print(f"     DexScreener: {BLUE}{links.get('dexscreener', 'N/A')}{RESET}")
            print(f"     DexTools:    {BLUE}{links.get('dextools', 'N/A')}{RESET}")
            print(f"     PooCoin:     {BLUE}{links.get('poocoin', 'N/A')}{RESET}")
            
            print(f"\n  {BOLD}🛡️ SÉCURITÉ:{RESET}")
            print(f"     Honeypot.is:  {BLUE}{links.get('honeypot_is', 'N/A')}{RESET}")
            print(f"     TokenSniffer: {BLUE}{links.get('tokensniffer', 'N/A')}{RESET}")
        
        elif d['chain'] == 'BSC':
            print(f"\n  {BOLD}📊 EXPLORATEURS:{RESET}")
            print(f"     BSCScan Token: {BLUE}{links.get('bscscan_token', 'N/A')}{RESET}")
            print(f"     BSCScan Pair:  {BLUE}{links.get('bscscan_pair', 'N/A')}{RESET}")
            
            print(f"\n  {BOLD}💱 DEX & TRADING:{RESET}")
            print(f"     PancakeSwap: {BLUE}{links.get('pancakeswap', 'N/A')}{RESET}")
            
            print(f"\n  {BOLD}📈 CHARTS:{RESET}")
            print(f"     DexScreener: {BLUE}{links.get('dexscreener', 'N/A')}{RESET}")
            print(f"     DexTools:    {BLUE}{links.get('dextools', 'N/A')}{RESET}")
            print(f"     PooCoin:     {BLUE}{links.get('poocoin', 'N/A')}{RESET}")
            
            print(f"\n  {BOLD}🛡️ SÉCURITÉ:{RESET}")
            print(f"     Honeypot.is:  {BLUE}{links.get('honeypot_is', 'N/A')}{RESET}")
            print(f"     TokenSniffer: {BLUE}{links.get('tokensniffer', 'N/A')}{RESET}")
            print(f"     RugCheck:     {BLUE}{links.get('rugcheck', 'N/A')}{RESET}")
        
        print(f"\n{BOLD}{BLUE}{'─'*116}{RESET}")
        print(f"\n{BOLD}{CYAN}📋 RÉSUMÉ RAPIDE{RESET}")
        print(f"  💰 Liquidité: ${d.get('liquidity_usd', 0):,.0f}")
        print(f"  💵 Prix: ${d.get('price_usd', 0):.8f}")
        print(f"  📊 Market Cap: ${d.get('market_cap_usd', 0):,.0f}")
        print(f"  ⚠️  Risque: {risk}/100")
        buy_link = links.get('uniswap') or links.get('pancakeswap') or 'N/A'
        print(f"  🔗 Achat: {GREEN}{buy_link}{RESET}")
        
        print("\n" + "="*120 + "\n")
    
    async def _get_complete_token_info(self, chain: str, token_address: str, pair_address: str, dex: str, w3: Web3) -> dict:
        """Récupère toutes les informations du token"""
        try:
            token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
            pair_contract = w3.eth.contract(address=Web3.to_checksum_address(pair_address), abi=PAIR_ABI)
            
            # Infos de base
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            decimals = token_contract.functions.decimals().call()
            total_supply = token_contract.functions.totalSupply().call()
            
            # Owner
            try:
                owner_address = token_contract.functions.owner().call()
                ownership_renounced = (owner_address == '0x0000000000000000000000000000000000000000')
                owner_balance = token_contract.functions.balanceOf(owner_address).call()
                owner_balance_pct = (owner_balance / total_supply * 100) if total_supply > 0 else 0
            except:
                owner_address = "N/A"
                ownership_renounced = True
                owner_balance_pct = 0
            
            # Réserves
            reserves = pair_contract.functions.getReserves().call()
            token0_address = pair_contract.functions.token0().call()
            
            wrapped_native = WRAPPED_NATIVE.get(chain)
            if token0_address.lower() == wrapped_native.lower():
                liquidity_native = reserves[0] / 10**18
                token_reserve = reserves[1] / 10**decimals
            else:
                liquidity_native = reserves[1] / 10**18
                token_reserve = reserves[0] / 10**decimals
            
            # Prix
            native_price_usd = NATIVE_PRICES.get(chain, 2000)
            liquidity_usd = liquidity_native * native_price_usd
            
            if token_reserve > 0:
                token_price_native = liquidity_native / token_reserve
                token_price_usd = token_price_native * native_price_usd
            else:
                token_price_usd = 0
            
            # Market cap
            total_supply_float = total_supply / 10**decimals
            market_cap_usd = total_supply_float * token_price_usd
            
            # Sécurité (analyse bytecode)
            bytecode = w3.eth.get_code(Web3.to_checksum_address(token_address)).hex()
            has_mint = 'mint' in bytecode.lower() or '40c10f19' in bytecode
            has_pause = 'pause' in bytecode.lower() or '8456cb59' in bytecode
            has_blacklist = any(x in bytecode.lower() for x in ['blacklist', 'block', 'banned'])
            has_proxy = 'delegatecall' in bytecode.lower()
            
            # Calcul du score de risque
            risk_score = 0
            if not ownership_renounced:
                risk_score += 20
            if has_mint:
                risk_score += 15
            if has_blacklist:
                risk_score += 25
            if owner_balance_pct > 20:
                risk_score += 15
            if liquidity_usd < 10000:
                risk_score += 15
            elif liquidity_usd < 5000:
                risk_score += 10
            
            return {
                "name": name,
                "symbol": symbol,
                "decimals": decimals,
                "total_supply": total_supply,
                "total_supply_formatted": f"{total_supply_float:,.0f}",
                "liquidity_native": liquidity_native,
                "liquidity_usd": liquidity_usd,
                "native_token": "ETH" if chain == "ETH" else "BNB",
                "price_usd": token_price_usd,
                "price_native": token_price_native if token_reserve > 0 else 0,
                "market_cap_usd": market_cap_usd,
                "owner_address": owner_address,
                "owner_balance_percent": owner_balance_pct,
                "ownership_renounced": ownership_renounced,
                "has_mint_function": has_mint,
                "has_pause_function": has_pause,
                "has_blacklist": has_blacklist,
                "has_proxy": has_proxy,
                "risk_score": min(risk_score, 100),
                "contract_verified": False,
                "lp_locked": False,
                "can_buy": True,
                "can_sell": True,
                "buy_tax": 0,
                "sell_tax": 0,
                "age_seconds": 0
            }
            
        except Exception as e:
            logger.warning(f"Failed to get token info: {e}")
            return {"liquidity_usd": 0}
    
    async def _should_analyze(self, token_info: dict) -> bool:
        return token_info.get("liquidity_usd", 0) >= self.min_liquidity_usd
    
    async def _print_stats(self):
        """Statistiques périodiques"""
        while self.running:
            await asyncio.sleep(60)
            
            print(f"\n📊 STATISTIQUES - {datetime.utcnow().strftime('%H:%M:%S')}")
            print(f"  Total détecté: {self.total_detections}")
            for chain in self.chains:
                block = self.last_scanned_blocks.get(chain, 0)
                print(f"  {chain}: Bloc #{block}")
            print()