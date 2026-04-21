import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

serve(async (req) => {
  try {
    const { record } = await req.json()
    
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // 1. Fetch the market mid-price for the associated option
    const { data: marketData, error: marketError } = await supabase
      .from('market_data')
      .select('mid_price')
      .eq('option_id', record.option_id)
      .order('trade_date', { ascending: false })
      .limit(1)
      .single()

    if (marketError || !marketData) {
      return new Response(JSON.stringify({ message: "No market data found" }), { status: 200 })
    }

    const computedPrice = record.computed_price
    const marketPrice = marketData.mid_price
    
    if (marketPrice === 0) return new Response(null, { status: 200 })

    const absoluteError = Math.abs(computedPrice - marketPrice)
    const relativePctError = (absoluteError / marketPrice) * 100

    // 2. Insert into validation_metrics
    await supabase.from('validation_metrics').upsert({
      option_id: record.option_id,
      method_result_id: record.id,
      absolute_error: absoluteError,
      relative_pct_error: relativePctError,
      mape: relativePctError,
      market_deviation: computedPrice - marketPrice
    })

    return new Response(JSON.stringify({ status: "success" }), { status: 200 })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  }
})
