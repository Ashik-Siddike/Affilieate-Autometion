"""
n8n Facebook Auto-Posting Test Script
এই script দিয়ে আপনি test করতে পারবেন যে n8n workflow ঠিকমতো Facebook-এ post করছে কিনা
"""

import requests
import json
from config import N8N_WEBHOOK_URL
from n8n_handler import trigger_n8n_workflow

def test_n8n_facebook_posting():
    """
    Tests n8n workflow for Facebook auto-posting
    """
    print("="*70)
    print("🧪 n8n Facebook Auto-Posting Test")
    print("="*70)
    print(f"\n📡 Webhook URL: {N8N_WEBHOOK_URL}\n")
    
    # Test data
    test_data = {
        'title': 'Test Product: Retro Gaming Console 2025',
        'amazon_link': 'https://automation-project.cstjpi.xyz/test-post',
        'image_url': 'https://via.placeholder.com/600x400?text=Test+Product',
        'social_caption': '🎮 Check out this amazing retro gaming console! #gaming #retro #review',
        'category': 'Gaming',
        'long_description': '''
        <h2>Test Product Review</h2>
        <p>This is a test review for the retro gaming console. It features excellent build quality, 
        great performance, and amazing value for money. Perfect for gaming enthusiasts who want 
        to relive their childhood memories.</p>
        <h3>Key Features:</h3>
        <ul>
            <li>High-quality display</li>
            <li>Long battery life</li>
            <li>Thousands of pre-loaded games</li>
            <li>Portable design</li>
        </ul>
        <p>This product is highly recommended for anyone looking for a great retro gaming experience.</p>
        '''
    }
    
    print("📦 Test Payload:")
    print(f"   Title: {test_data['title']}")
    print(f"   Category: {test_data['category']}")
    print(f"   Amazon Link: {test_data['amazon_link']}\n")
    
    print("🔄 Sending test data to n8n workflow...\n")
    
    # Call the n8n handler
    success = trigger_n8n_workflow(
        title=test_data['title'],
        amazon_link=test_data['amazon_link'],
        image_url=test_data['image_url'],
        social_caption=test_data['social_caption'],
        category=test_data['category'],
        long_description=test_data['long_description']
    )
    
    print("\n" + "="*70)
    if success:
        print("✅ TEST PASSED!")
        print("="*70)
        print("\n📋 Next Steps:")
        print("   1. Check your n8n dashboard: https://ashik-mama.app.n8n.cloud")
        print("   2. Go to 'Executions' tab to see the workflow execution")
        print("   3. Check your Facebook page to verify the post was published")
        print("   4. If Facebook post is not visible, check:")
        print("      - Facebook credentials in n8n are configured correctly")
        print("      - Facebook page permissions are set correctly")
        print("      - Workflow nodes are properly connected")
    else:
        print("❌ TEST FAILED!")
        print("="*70)
        print("\n🔍 Troubleshooting:")
        print("   1. Check if workflow is ACTIVE in n8n dashboard")
        print("   2. Verify webhook URL is correct in config.py")
        print("   3. Check n8n instance is running and accessible")
        print("   4. Review error messages above for specific issues")
    print("="*70)

if __name__ == "__main__":
    test_n8n_facebook_posting()


