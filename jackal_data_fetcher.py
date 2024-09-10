import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JackalDataFetcher:
    def __init__(self, api_url):
        self.api_url = api_url

    async def fetch_data(self, endpoint):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}{endpoint}", ssl=False) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error fetching data from {endpoint}: {response.status}")
                    return None

    async def get_latest_block(self):
        data = await self.fetch_data("cosmos/base/tendermint/v1beta1/blocks/latest")
        if data:
            return {
                "height": int(data['block']['header'].get('height', 0)),
                "time": data['block']['header'].get('time', None)
            }
        return None

    async def get_block(self, height):
        data = await self.fetch_data(f"cosmos/base/tendermint/v1beta1/blocks/{height}")
        if data:
            return {
                "height": int(data['block']['header'].get('height', 0)),
                "time": data['block']['header'].get('time', None)
            }
        return None

    async def get_validator_set(self):
        data = await self.fetch_data("cosmos/base/tendermint/v1beta1/validatorsets/latest")
        if data:
            return [{"address": v['address'], "voting_power": v['voting_power']} for v in data.get('validators', [])]
        return None

    async def get_inflation_rate(self):
        data = await self.fetch_data("cosmos/mint/v1beta1/inflation")
        if data:
            return float(data.get('inflation', '0'))
        return None

    async def get_governance_proposals(self):
        data = await self.fetch_data("cosmos/gov/v1beta1/proposals")
        if data:
            return [
                {"id": p['proposal_id'], "title": p['content']['title'], "status": p['status']}
                for p in data.get('proposals', [])
                if p['status'] == "PROPOSAL_STATUS_VOTING_PERIOD"
            ]
        return None

    async def get_network_stats(self):
        latest_block = await self.get_latest_block()
        validator_set = await self.get_validator_set()
        inflation_rate = await self.get_inflation_rate()
        proposals = await self.get_governance_proposals()

        return {
            "latest_block": latest_block,
            "active_validators": len(validator_set) if validator_set else None,
            "inflation_rate": inflation_rate,
            "active_proposals": len(proposals) if proposals else 0
        }