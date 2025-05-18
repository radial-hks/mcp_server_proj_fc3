from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
from typing import List, Dict, Any, Annotated # Add Annotated
from pydantic import BaseModel, Field # Add Field
from core.transformation import CoordinateTransformer # Assuming core.transformation is in the same directory level

mcp = FastMCP("Coordinate Transform App")

@mcp.tool()
async def hello() -> str:
    """Return string 'Hello World!'"""
    print("hello tool called")
    return f"Hello World!"

# Define Pydantic model for a single coordinate
class CoordinateItem(BaseModel):
    x: Annotated[float, Field(description="X坐标值")]
    y: Annotated[float, Field(description="Y坐标值")]

@mcp.tool(
    name="transform_coordinates",
    description="在不同坐标系统之间转换坐标，支持EPSG、WKT和Proj格式的坐标系统",
)
async def transform_coordinates(
    source_crs: Annotated[str, Field(description='源坐标系统，支持EPSG、WKT和Proj格式，例如："EPSG:4326" 或 "+proj=longlat +datum=WGS84"')], 
    target_crs: Annotated[str, Field(description='目标坐标系统，支持EPSG、WKT和Proj格式，例如："EPSG:3857" 或 "+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +no_defs"')], 
    coordinates: Annotated[List[CoordinateItem], Field(description="要转换的坐标列表，每个坐标包含x和y值", min_items=1)]
) -> str:
    """处理坐标转换请求"""
    # if not all([source_crs, target_crs, coordinates]):
    #     # FastMCP might handle this based on schema, but explicit check is good.
    #     # However, FastMCP expects the function to raise an error or return a value.
    #     # For simplicity, we'll let FastMCP handle missing args based on schema if possible,
    #     # or rely on the CoordinateTransformer to raise errors for invalid CRS.
    #     # For now, let's assume valid inputs as per schema.
    #     pass
    transformer = CoordinateTransformer()
    try:
        transformer.set_source_crs(source_crs)
        transformer.set_target_crs(target_crs)
        transformer.initialize_transformer()

        results_log = []
        for coord in coordinates:
            x, y = coord.x, coord.y # Use Pydantic model attributes
            try:
                trans_x, trans_y = transformer.transform_point(x, y)
                results_log.append(
                    f"输入: ({x}, {y})\n输出: ({trans_x:.8f}, {trans_y:.8f})"
                )
            except ValueError as e:
                results_log.append(
                    f"输入: ({x}, {y})\n错误: {str(e)}"
                )
        
        return f"坐标转换结果 (从 {source_crs} 到 {target_crs}):\n" + "\n".join(results_log)

    except ValueError as e:
        # FastMCP tools should ideally return a string or raise an error that FastMCP can handle.
        # Returning an error message string is one way.
        return f"坐标转换失败: {str(e)}"


app = Starlette(
    routes=[
        Mount('/', app=mcp.sse_app()),
    ]
)