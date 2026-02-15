"""
Test PDF reading functionality
"""
import asyncio
from tool_logic import ToolExecutor

async def test_pdf_read():
    """Test reading a PDF file"""
    
    pdf_path = r"C:\Users\RanVic\.agent-workspace\projects\7f7856d1-2ac3-4750-a739-a4d954f582ae\01_Application_Forms\ABE Application Form Good - Annex.3 Medical History (1).pdf"
    
    print(f"Testing PDF read for: {pdf_path}")
    print("=" * 80)
    
    executor = ToolExecutor()
    
    result = await executor.execute("read_file", {"path": pdf_path})
    
    print(f"\nSuccess: {result.success}")
    print(f"Execution time: {result.execution_time_ms:.2f}ms")
    
    if result.success:
        print(f"\nFile type: {result.result.get('file_type')}")
        print(f"Size: {result.result.get('size_bytes')} bytes")
        
        if 'pages' in result.result:
            print(f"Pages: {result.result.get('pages')}")
        
        content = result.result.get('content', '')
        print(f"\nContent length: {len(content)} characters")
        print("\n--- First 1000 characters ---")
        print(content[:1000])
        print("\n--- Last 500 characters ---")
        print(content[-500:])
    else:
        print(f"\nError: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_pdf_read())
