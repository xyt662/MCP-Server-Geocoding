#!/usr/bin/env python3
"""MCP Server Geocoding API 使用示例"""

import asyncio
import httpx
import json
from typing import Dict, Any


class GeocodingClient:
    """地理编码客户端示例"""
    
    def __init__(self, base_url: str = "http://localhost:4000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    async def geocode(self, address: str, city: str = None) -> Dict[str, Any]:
        """地理编码"""
        data = {"address": address}
        if city:
            data["city"] = city
        
        response = await self.client.post(
            f"{self.base_url}/geocode",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def reverse_geocode(self, latitude: float, longitude: float, radius: int = 1000) -> Dict[str, Any]:
        """逆地理编码"""
        data = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius
        }
        
        response = await self.client.post(
            f"{self.base_url}/reverse-geocode",
            json=data
        )
        response.raise_for_status()
        return response.json()


async def basic_examples():
    """基础使用示例"""
    client = GeocodingClient()
    
    try:
        print("=== MCP Server Geocoding API 示例 ===")
        
        # 1. 健康检查
        print("\n1. 健康检查")
        health = await client.health_check()
        print(f"服务状态: {health['status']}")
        
        # 2. 地理编码示例
        print("\n2. 地理编码示例")
        addresses = [
            "北京市朝阳区三里屯",
            "上海市浦东新区陆家嘴",
            "广州市天河区珠江新城",
            "深圳市南山区科技园"
        ]
        
        for address in addresses:
            try:
                result = await client.geocode(address)
                print(f"地址: {address}")
                print(f"  坐标: ({result['latitude']}, {result['longitude']})")
                print(f"  格式化地址: {result['formatted_address']}")
                print(f"  置信度: {result.get('confidence', 'N/A')}")
                print()
            except Exception as e:
                print(f"地理编码失败 - {address}: {e}")
        
        # 3. 逆地理编码示例
        print("\n3. 逆地理编码示例")
        coordinates = [
            (39.9042, 116.4074),  # 北京天安门
            (31.2304, 121.4737),  # 上海外滩
            (23.1291, 113.2644),  # 广州塔
            (22.5431, 114.0579),  # 深圳市民中心
        ]
        
        for lat, lng in coordinates:
            try:
                result = await client.reverse_geocode(lat, lng)
                print(f"坐标: ({lat}, {lng})")
                print(f"  地址: {result['address']}")
                print(f"  国家: {result.get('country', 'N/A')}")
                print(f"  省份: {result.get('province', 'N/A')}")
                print(f"  城市: {result.get('city', 'N/A')}")
                print(f"  置信度: {result.get('confidence', 'N/A')}")
                print()
            except Exception as e:
                print(f"逆地理编码失败 - ({lat}, {lng}): {e}")
    
    finally:
        await client.close()


async def batch_geocoding_example():
    """批量地理编码示例"""
    client = GeocodingClient()
    
    try:
        print("\n=== 批量地理编码示例 ===")
        
        addresses = [
            "北京市海淀区中关村",
            "上海市黄浦区南京路",
            "广州市越秀区北京路",
            "深圳市福田区华强北",
            "杭州市西湖区西湖",
            "成都市锦江区春熙路",
            "武汉市武昌区户部巷",
            "西安市雁塔区大雁塔"
        ]
        
        # 并发处理
        tasks = [client.geocode(address) for address in addresses]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"处理了 {len(addresses)} 个地址:")
        for i, (address, result) in enumerate(zip(addresses, results)):
            if isinstance(result, Exception):
                print(f"{i+1:2d}. {address} - 失败: {result}")
            else:
                print(f"{i+1:2d}. {address}")
                print(f"    坐标: ({result['latitude']:.4f}, {result['longitude']:.4f})")
    
    finally:
        await client.close()


async def error_handling_example():
    """错误处理示例"""
    client = GeocodingClient()
    
    try:
        print("\n=== 错误处理示例 ===")
        
        # 1. 无效地址
        print("\n1. 测试无效地址")
        try:
            result = await client.geocode("这是一个不存在的地址12345")
            print(f"意外成功: {result}")
        except httpx.HTTPStatusError as e:
            print(f"预期的错误: {e.response.status_code} - {e.response.text}")
        
        # 2. 空地址
        print("\n2. 测试空地址")
        try:
            result = await client.geocode("")
            print(f"意外成功: {result}")
        except httpx.HTTPStatusError as e:
            print(f"预期的错误: {e.response.status_code}")
        
        # 3. 无效坐标
        print("\n3. 测试无效坐标")
        try:
            result = await client.reverse_geocode(91, 181)  # 超出有效范围
            print(f"意外成功: {result}")
        except httpx.HTTPStatusError as e:
            print(f"预期的错误: {e.response.status_code}")
    
    finally:
        await client.close()


async def performance_test():
    """性能测试示例"""
    client = GeocodingClient()
    
    try:
        print("\n=== 性能测试示例 ===")
        
        # 测试地理编码性能
        address = "北京市朝阳区三里屯"
        num_requests = 10
        
        print(f"\n测试地理编码性能 - {num_requests} 次请求")
        start_time = asyncio.get_event_loop().time()
        
        tasks = [client.geocode(address) for _ in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = num_requests - successful
        
        print(f"总时间: {duration:.2f}秒")
        print(f"平均响应时间: {duration/num_requests*1000:.2f}ms")
        print(f"成功: {successful}, 失败: {failed}")
        print(f"QPS: {num_requests/duration:.2f}")
    
    finally:
        await client.close()


def sync_example():
    """同步调用示例"""
    print("\n=== 同步调用示例 ===")
    
    # 使用httpx同步客户端
    with httpx.Client(timeout=30.0) as client:
        # 健康检查
        response = client.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("服务健康")
        
        # 地理编码
        response = client.post(
            "http://localhost:8000/geocode",
            json={"address": "北京市朝阳区三里屯"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"地理编码结果: ({result['latitude']}, {result['longitude']})")
        else:
            print(f"地理编码失败: {response.status_code}")


async def main():
    """主函数"""
    print("MCP Server Geocoding API 使用示例")
    print("请确保服务器正在运行: python start.py")
    print("API文档: http://localhost:8000/docs")
    
    try:
        await basic_examples()
        await batch_geocoding_example()
        await error_handling_example()
        await performance_test()
        sync_example()
    except httpx.ConnectError:
        print("\n错误: 无法连接到服务器")
        print("请确保服务器正在运行: python start.py")
    except Exception as e:
        print(f"\n未预期的错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())