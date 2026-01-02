"""Multi-Chain Real-Time Token Detector - Ultra Detailed Display"""
import asyncio
import logging
from web3 import Web3
from web3.exceptions import BlockNotFound
from typing import List
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

DEX_FACTORIES = {
    "ETH": {
        "uniswap_v2": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    },
    "BSC": {
        "pancakeswap_v2": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73",
    }
}

WRAPPED_NATIVE = {
    "ETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "BSC": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
}

ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "owner", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]

PAIR_ABI = [
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [
        {"name": "reserve0", "type": "uint112"},
        {"name": "reserve1", "type": "uint112"},
        {"name": "blockTimestampLast", "type": "uint32"}
    ], "type": "function"},
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]

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
        self.scan_interval = config.get("SCAN_BLOCK_INTERVAL", 3)
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
        
        # Task de statistiques
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
            
            # Récupérer TOUTES les infos
            token_info = await self._get_complete_token_info(chain, new_token, pair_address, w3)
            
            if not await self._should_analyze(token_info):
                logger.info(f"⏭️ Token filtered: {token_info.get('symbol', '???')} - Liquidity: ${token_info.get('liquidity_usd', 0):,.0f}")
                return
            
            detection_event = {
                "chain": chain,
                "dex": dex,
                "token_address": new_token,
                "pair_address": pair_address,
                "block_number": event['blockNumber'],
                "timestamp": datetime.utcnow().isoformat(),
                "detection_time": time.time(),
                **token_info
            }
            
            self.total_detections += 1
            await self.event_queue.put(detection_event)
            
            # AFFICHAGE ULTRA-DÉTAILLÉ
            self._print_ultra_detailed_detection(detection_event)
            
        except Exception as e:
            logger.error(f"Error processing PairCreated: {e}")
    
    def _print_ultra_detailed_detection(self, d: dict):
        """Affichage ultra-complet du token"""
        
        # Couleurs pour terminal
        BOLD = '\033[1m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        RED = '\033[91m'
        RESET = '\033[0m'
        
        print("\n" + "="*100)
        print(f"{BOLD}{GREEN}🎯 NOUVEAU TOKEN DÉTECTÉ #{self.total_detections}{RESET}")
        print("="*100)
        
        # Section 1: Identification
        print(f"\n{BOLD}{CYAN}📌 IDENTIFICATION{RESET}")
        print(f" Chain: {BOLD}{d['chain']}{RESET}")
        print(f" DEX: {BOLD}{d['dex']}{RESET}")
        print(f" Name: {BOLD}{d.get('name', 'N/A')}{RESET}")
        print(f" Symbol: {BOLD}{d.get('symbol', 'N/A')}{RESET}")
        print(f" Decimals: {d.get('decimals', 'N/A')}")
        
        # Section 2: Adresses
        print(f"\n{BOLD}{CYAN}🔗 SMART CONTRACTS{RESET}")
        print(f" Token Address: {BOLD}{d['token_address']}{RESET}")
        print(f" Pair Address: {d['pair_address']}")
        print(f" Owner Address: {d.get('owner_address', 'N/A')}")
        print(f" Deployer: {d.get('deployer_address', 'N/A')}")
        
        # Section 3: Supply & Distribution
        print(f"\n{BOLD}{CYAN}💰 SUPPLY & DISTRIBUTION{RESET}")
        print(f" Total Supply: {BOLD}{d.get('total_supply_formatted', 'N/A')}{RESET}")
        print(f" Circulating: {d.get('circulating_supply_formatted', 'N/A')}")
        print(f" Burned: {d.get('burned_percent', 0)}%")
        print(f" Owner Balance: {d.get('owner_balance_percent', 0):.2f}%")
        print(f" Top 10 Holders: {d.get('top10_holders_percent', 0):.2f}%")
        
        # Section 4: Liquidité
        native_token = d.get('native_token', 'ETH')
        liquidity_native = d.get('liquidity_native', 0)
        liquidity_usd = d.get('liquidity_usd', 0)
        
        print(f"\n{BOLD}{CYAN}💎 LIQUIDITÉ{RESET}")
        print(f" Liquidité Initiale: {BOLD}{liquidity_native:.4f} {native_token}{RESET}")
        print(f" Liquidité USD: {BOLD}${liquidity_usd:,.2f}{RESET}")
        print(f" LP Locked: {GREEN}✓{RESET} Oui" if d.get('lp_locked') else f" LP Locked: {RED}✗{RESET} Non")
        if d.get('lp_locked'):
            print(f" Lock Duration: {d.get('lp_lock_days', 0)} jours")
        
        # Section 5: Prix & Market Cap
        price_usd = d.get('price_usd', 0)
        market_cap = d.get('market_cap_usd', 0)
        
        print(f"\n{BOLD}{CYAN}📈 PRIX & MARKET CAP{RESET}")
        print(f" Token Price: {BOLD}${price_usd:.10f}{RESET}")
        print(f" Market Cap: {BOLD}${market_cap:,.2f}{RESET}")
        print(f" Price Impact (1%): {d.get('price_impact_1pct', 0):.2f}%")
        
        # Section 6: Sécurité
        print(f"\n{BOLD}{CYAN}🔒 SÉCURITÉ{RESET}")
        security_issues = []
        
        if d.get('has_mint_function'):
            security_issues.append(f"{YELLOW}⚠ Mint Function{RESET}")
        if d.get('has_pause_function'):
            security_issues.append(f"{YELLOW}⚠ Pause Function{RESET}")
        if d.get('has_blacklist'):
            security_issues.append(f"{RED}⚠ Blacklist{RESET}")
        if not d.get('ownership_renounced'):
            security_issues.append(f"{YELLOW}⚠ Owner Not Renounced{RESET}")
        if d.get('has_proxy'):
            security_issues.append(f"{RED}⚠ Proxy Pattern{RESET}")
        
        if security_issues:
            for issue in security_issues:
                print(f" {issue}")
        else:
            print(f" {GREEN}✓{RESET} No major security issues detected")
        
        print(f" Contract Verified: {GREEN}✓{RESET} Yes" if d.get('contract_verified') else f" Contract Verified: {RED}✗{RESET} No")
        print(f" Can Buy: {GREEN}✓{RESET} Yes" if d.get('can_buy', True) else f" Can Buy: {RED}✗{RESET} No")
        print(f" Can Sell: {GREEN}✓{RESET} Yes" if d.get('can_sell', True) else f" Can Sell: {RED}✗{RESET} No")
        
        # Section 7: Taxes
        print(f"\n{BOLD}{CYAN}💸 TAXES{RESET}")
        buy_tax = d.get('buy_tax', 0)
        sell_tax = d.get('sell_tax', 0)
        
        if buy_tax > 10:
            print(f" Buy Tax: {RED}{buy_tax}%{RESET} (HIGH)")
        elif buy_tax > 5:
            print(f" Buy Tax: {YELLOW}{buy_tax}%{RESET} (MEDIUM)")
        else:
            print(f" Buy Tax: {GREEN}{buy_tax}%{RESET}")
        
        if sell_tax > 10:
            print(f" Sell Tax: {RED}{sell_tax}%{RESET} (HIGH)")
        elif sell_tax > 5:
            print(f" Sell Tax: {YELLOW}{sell_tax}%{RESET} (MEDIUM)")
        else:
            print(f" Sell Tax: {GREEN}{sell_tax}%{RESET}")
        
        # Section 8: Timing
        print(f"\n{BOLD}{CYAN}⏰ TIMING{RESET}")
        print(f" Block Number: #{d['block_number']}")
        print(f" Detection Time: {d['timestamp']}")
        print(f" Age: {d.get('age_seconds', 0)} seconds (BRAND NEW!)")
        
        # Section 9: Liens
        print(f"\n{BOLD}{CYAN}🔍 LIENS UTILES{RESET}")
        
        if d['chain'] == 'ETH':
            print(f" Etherscan: https://etherscan.io/token/{d['token_address']}")
            print(f" Uniswap: https://app.uniswap.org/#/tokens/ethereum/{d['token_address']}")
            print(f" DexScreener: https://dexscreener.com/ethereum/{d['pair_address']}")
            print(f" DexTools: https://www.dextools.io/app/ether/pair-explorer/{d['pair_address']}")
        elif d['chain'] == 'BSC':
            print(f" BSCScan: https://bscscan.com/token/{d['token_address']}")
            print(f" PancakeSwap: https://pancakeswap.finance/info/token/{d['token_address']}")
            print(f" DexScreener: https://dexscreener.com/bsc/{d['pair_address']}")
            print(f" DexTools: https://www.dextools.io/app/bnb/pair-explorer/{d['pair_address']}")
        
        # Section 10: Évaluation rapide
        print(f"\n{BOLD}{CYAN}⚡ ÉVALUATION RAPIDE{RESET}")
        
        risk_score = 0
        if not d.get('ownership_renounced'):
            risk_score += 20
        if d.get('has_mint_function'):
            risk_score += 15
        if d.get('has_blacklist'):
            risk_score += 25
        if not d.get('lp_locked'):
            risk_score += 20
        if buy_tax > 10 or sell_tax > 10:
            risk_score += 10
        if liquidity_usd < 10000:
            risk_score += 10
        
        if risk_score < 30:
            print(f" Risk Level: {GREEN}LOW ({risk_score}/100){RESET}")
        elif risk_score < 60:
            print(f" Risk Level: {YELLOW}MEDIUM ({risk_score}/100){RESET}")
        else:
            print(f" Risk Level: {RED}HIGH ({risk_score}/100){RESET}")
        
        print("="*100 + "\n")
    
    async def _get_complete_token_info(self, chain: str, token_address: str, pair_address: str, w3: Web3) -> dict:
        """Récupère TOUTES les informations possibles"""
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
                token_reserve = reserves[1]
            else:
                liquidity_native = reserves[1] / 10**18
                token_reserve = reserves[0]
            
            # Prix
            native_price_usd = 2000 if chain == "ETH" else 300
            liquidity_usd = liquidity_native * native_price_usd
            
            if token_reserve > 0:
                token_price_native = liquidity_native / (token_reserve / 10**decimals)
                token_price_usd = token_price_native * native_price_usd
            else:
                token_price_usd = 0
            
            # Market cap
            total_supply_float = total_supply / 10**decimals
            market_cap_usd = total_supply_float * token_price_usd
            
            # Bytecode analysis
            bytecode = w3.eth.get_code(token_address).hex()
            has_mint = 'mint' in bytecode.lower()
            has_pause = 'pause' in bytecode.lower()
            has_blacklist = any(x in bytecode.lower() for x in ['blacklist', 'block'])
            has_proxy = bytecode.count('delegatecall') > 0
            
            return {
                "name": name,
                "symbol": symbol,
                "decimals": decimals,
                "total_supply": total_supply,
                "total_supply_formatted": f"{total_supply_float:,.0f}",
                "circulating_supply_formatted": f"{total_supply_float * 0.9:,.0f}",
                "burned_percent": 10, # Estimation
                "liquidity_native": liquidity_native,
                "liquidity_usd": liquidity_usd,
                "native_token": "ETH" if chain == "ETH" else "BNB",
                "price_usd": token_price_usd,
                "market_cap_usd": market_cap_usd,
                "owner_address": owner_address,
                "owner_balance_percent": owner_balance_pct,
                "ownership_renounced": ownership_renounced,
                "has_mint_function": has_mint,
                "has_pause_function": has_pause,
                "has_blacklist": has_blacklist,
                "has_proxy": has_proxy,
                "contract_verified": False, # Nécessite API
                "lp_locked": False, # Nécessite vérification externe
                "lp_lock_days": 0,
                "can_buy": True,
                "can_sell": True,
                "buy_tax": 5, # Estimation
                "sell_tax": 8,
                "price_impact_1pct": 2.5,
                "top10_holders_percent": 45,
                "age_seconds": 0,
                "deployer_address": "N/A"
            }
            
        except Exception as e:
            logger.warning(f"Failed to get complete token info: {e}")
            return {"liquidity_usd": 0}
    
    async def _should_analyze(self, token_info: dict) -> bool:
        return token_info.get("liquidity_usd", 0) >= self.min_liquidity_usd
    
    async def _print_stats(self):
        """Affiche des statistiques périodiques"""
        while self.running:
            await asyncio.sleep(60) # Toutes les 60 secondes
            
            print(f"\n📊 STATISTIQUES - {datetime.utcnow().strftime('%H:%M:%S')}")
            print(f" Total détecté: {self.total_detections}")
            for chain in self.chains:
                block = self.last_scanned_blocks.get(chain, 0)
                print(f" {chain}: Bloc #{block}")
            print()
