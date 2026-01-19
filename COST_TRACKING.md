# 💰 Cost Tracking Guide

## Overview

The API now automatically tracks **all costs** for:
- OpenAI GPT prompt generation
- Google Gemini image generation

Every job includes detailed cost breakdown!

---

## 📊 What's Tracked

### Per Job

Each job tracks:

```json
{
  "id": "job-123",
  "status": "completed",
  "cost": {
    "prompt_generation_cost": 0.00045,    // OpenAI cost
    "image_generation_cost": 0.00576,      // Gemini cost
    "total_cost": 0.00621,                 // Combined
    "prompt_tokens_used": 3542,            // GPT tokens
    "image_tokens_used": 23220,            // Gemini tokens (approx)
    "num_prompts_generated": 18,           // Scenes processed
    "num_images_generated": 18             // Images created
  }
}
```

### Live Tracking

Costs update in real-time as the job processes!

---

## 🎯 How to Check Costs

### Option 1: Get Job Details

```bash
curl http://localhost:8000/jobs/{job_id}
```

**Response:**
```json
{
  "id": "abc-123",
  "status": "completed",
  "cost": {
    "total_cost": 0.00621,
    "prompt_generation_cost": 0.00045,
    "image_generation_cost": 0.00576,
    "prompt_tokens_used": 3542,
    "image_tokens_used": 23220,
    "num_prompts_generated": 18,
    "num_images_generated": 18
  },
  ...
}
```

### Option 2: Check Logs

When a job completes, the server logs:

```
✅ Job completed successfully: abc-123
💰 Total cost: $0.0062
   - Prompts: $0.0004 (3542 tokens)
   - Images: $0.0058 (18 images)
```

### Option 3: List All Jobs

```bash
curl http://localhost:8000/jobs
```

See costs for all jobs!

---

## 💵 Pricing Breakdown

### OpenAI (GPT-4o-mini)

**Current Model:** `gpt-4o-mini`

| Token Type | Cost |
|------------|------|
| Input | $0.150 / 1M tokens |
| Output | $0.600 / 1M tokens |

**Typical Scene:**
- ~150 input tokens (system + user prompt)
- ~200 output tokens (JSON visual prompt)
- **Cost per scene: ~$0.00015**

**Example:** 20 scenes = **$0.003** for prompts

### Google Gemini (Nano Banana)

**Current Model:** `gemini-2.5-flash-image`

| Model | Cost per Image |
|-------|----------------|
| Flash Image | $0.00032 |
| Pro Image 1K/2K | $0.00028 |
| Pro Image 4K | $0.00050 |

**Example:** 20 images = **$0.0064**

---

## 📈 Cost Estimation

### By Script Length

| Script Length | Est. Scenes | Prompt Cost | Image Cost | Total |
|--------------|-------------|-------------|------------|-------|
| Short (100 words) | ~5 scenes | $0.0008 | $0.0016 | **$0.0024** |
| Medium (300 words) | ~15 scenes | $0.0023 | $0.0048 | **$0.0071** |
| Long (500 words) | ~25 scenes | $0.0038 | $0.0080 | **$0.0118** |
| Very Long (1000 words) | ~50 scenes | $0.0075 | $0.0160 | **$0.0235** |

### Quick Formula

```
Estimated Cost = (num_scenes × $0.00015) + (num_images × $0.00032)
```

For most videos: **~$0.0005 per scene**

---

## 🎬 Real-World Examples

### Example 1: 60-Second Video

```
Script: 150 words
Scenes: 10
Prompts: $0.0015
Images: $0.0032
Total: $0.0047
```

**Monthly (30 videos):** ~$0.14

### Example 2: 3-Minute Video

```
Script: 450 words
Scenes: 30
Prompts: $0.0045
Images: $0.0096
Total: $0.0141
```

**Monthly (30 videos):** ~$0.42

### Example 3: 10-Minute Video

```
Script: 1500 words
Scenes: 100
Prompts: $0.0150
Images: $0.0320
Total: $0.0470
```

**Monthly (30 videos):** ~$1.41

---

## 💡 Cost Optimization Tips

### 1. Batch Processing

Process multiple scripts in one session:
```bash
# More efficient than generating one at a time
for script in script1.txt script2.txt script3.txt; do
  curl -X POST http://localhost:8000/jobs \
    -H "Content-Type: application/json" \
    -d "{\"script_text\": \"$(cat $script)\"}"
done
```

### 2. Disable Images for Drafts

Test your script without images first:

```json
{
  "script_text": "Your script...",
  "generate_images": false  // ← Save money on drafts!
}
```

Cost: **$0.0015** vs **$0.0047** (70% savings!)

### 3. Reuse Prompts

If you're happy with the visual prompts, regenerate only failed images:

```bash
POST /scenes/{scene_id}/regenerate-image
```

Cost: **$0.00032** per image only (no prompt cost!)

### 4. Shorter Sentences

Break long paragraphs into clear sentences:
- ❌ "And then I realized that the most important thing in life is not about what you achieve but rather how you treat the people around you and the impact you make on their lives."
- ✅ "I realized something important. It's not about what you achieve. It's about how you treat people."

**Result:** Better visuals, lower cost (1 scene vs 3 scenes)

---

## 📊 Monitoring Costs

### Track Your Monthly Usage

Create a simple tracking script:

```python
import requests
import json

# Get all jobs
response = requests.get('http://localhost:8000/jobs')
jobs = response.json()

# Calculate totals
total_cost = sum(job['cost']['total_cost'] for job in jobs)
total_prompts = sum(job['cost']['num_prompts_generated'] for job in jobs)
total_images = sum(job['cost']['num_images_generated'] for job in jobs)

print(f"📊 Usage Summary")
print(f"Total Jobs: {len(jobs)}")
print(f"Total Scenes: {total_prompts}")
print(f"Total Images: {total_images}")
print(f"💰 Total Cost: ${total_cost:.4f}")
print(f"📈 Average per Job: ${total_cost/len(jobs):.4f}")
```

### Set Budgets

Create alerts when costs exceed limits:

```python
def check_budget(job_id):
    response = requests.get(f'http://localhost:8000/jobs/{job_id}')
    job = response.json()
    
    if job['cost']['total_cost'] > 0.05:  # $0.05 limit
        print(f"⚠️ Warning: Job {job_id} cost ${job['cost']['total_cost']:.4f}")
        print(f"   Scenes: {job['cost']['num_prompts_generated']}")
        return False
    return True
```

---

## 🔍 Understanding the Breakdown

### Prompt Generation (OpenAI)

**What you're paying for:**
- System prompt (tells GPT how to format output)
- User prompt (your script sentence)
- JSON response (structured visual description)

**Typical tokens:**
- Input: ~150 tokens
- Output: ~200 tokens
- Total: ~350 tokens = **$0.00015**

### Image Generation (Gemini)

**What you're paying for:**
- Text-to-image generation
- 1024x1024 resolution (Flash model)
- SynthID watermark embedding
- C2PA metadata

**Cost:** ~1290 tokens = **$0.00032 per image**

---

## 💳 Free Tier Limits

### OpenAI

- **Free trial:** $5 credit
- **Limits:** Varies by account
- **Rate limits:** 3 requests/min (free tier)

**Your $5 gets you:** ~10,000 scenes!

### Google Gemini

- **Free tier:** 15 requests per minute
- **Daily limit:** 1500 requests
- **Monthly:** 1M tokens free

**Your free tier gets you:** ~775 images per day!

---

## 📈 Scaling Costs

### Small Creator (5 videos/week)

```
5 videos × 15 scenes each = 75 scenes/week
Cost per week: ~$0.04
Cost per month: ~$0.16
Cost per year: ~$1.92
```

### Medium Creator (1 video/day)

```
30 videos × 20 scenes each = 600 scenes/month
Cost per month: ~$0.30
Cost per year: ~$3.60
```

### Large Creator (3 videos/day)

```
90 videos × 25 scenes each = 2,250 scenes/month
Cost per month: ~$1.13
Cost per year: ~$13.56
```

**Bottom line:** Even at scale, costs are minimal! 🎉

---

## 🚨 Cost Alerts

The API logs costs automatically. Watch for:

```
✅ Job completed successfully: abc-123
💰 Total cost: $0.0062
```

If costs seem high:
1. Check number of scenes
2. Verify script length
3. Look for very long sentences
4. Consider breaking into shorter sentences

---

## 🔄 Cost for Regenerations

When you regenerate an image:

```bash
POST /scenes/{scene_id}/regenerate-image
```

**Cost added:**
- Prompt: **$0** (reuses existing)
- Image: **$0.00032** (generates new)

**Total:** Only pay for the new image!

---

## 📱 Display Costs in UI

Show users what they're spending:

```jsx
function JobCostDisplay({ job }) {
  const cost = job.cost;
  
  return (
    <div className="cost-breakdown">
      <h3>Cost: ${cost.total_cost.toFixed(4)}</h3>
      <ul>
        <li>Prompts: ${cost.prompt_generation_cost.toFixed(4)} 
            ({cost.num_prompts_generated} scenes)</li>
        <li>Images: ${cost.image_generation_cost.toFixed(4)} 
            ({cost.num_images_generated} images)</li>
      </ul>
      <p>Tokens: {cost.prompt_tokens_used + cost.image_tokens_used} total</p>
    </div>
  );
}
```

---

## 🎯 Key Takeaways

1. **Costs are automatic** - No manual tracking needed
2. **Very affordable** - ~$0.0005 per scene
3. **Transparent** - Full breakdown in every job
4. **Optimizable** - Disable images for drafts
5. **Scalable** - Costs stay low even at high volume

---

## 📞 Need Help?

- Check job costs: `GET /jobs/{job_id}`
- View all jobs: `GET /jobs`
- Check logs for cost breakdown
- Use test scripts to estimate costs

---

**Remember:** These are estimated costs based on current API pricing. Always check official pricing pages for the most up-to-date information!

- [OpenAI Pricing](https://openai.com/api/pricing/)
- [Google Gemini Pricing](https://ai.google.dev/pricing)

Happy creating! 💰🚀
