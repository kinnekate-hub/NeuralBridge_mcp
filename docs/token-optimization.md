# MCP Server Token Optimization

## Summary

NeuralBridge MCP server includes multiple token optimization strategies, all enabled by default. These reduce per-response token consumption by 40-70% depending on the operation, while keeping all functionality accessible.

**CLI flags** (ON by default, disable with `--no-*` flags):

| Flag | What it does | Estimated savings |
|------|-------------|-------------------|
| `--no-compact-tree` | Compact tabular UI tree → verbose JSON | 50-60% on get_ui_tree |
| `--no-filter-elements` | Filter to interactive elements → show all | 30-50% on get_ui_tree |
| `--no-compact-bounds` | `[l,t,r,b]` bounds → `{left,top,right,bottom}` | 15-20% on element data |
| `--no-consolidate` | Expose 4 redundant tools → remove them | ~1,000 tokens tool overhead |

**Always-on optimizations** (not configurable via CLI):

| Behavior | What it does | Estimated savings |
|----------|-------------|-------------------|
| Omit empty fields | Skip empty strings, false flags, generic class names in element JSON | 20-30% on element data |
| Strip `"success": true` | Omit redundant success field (MCP envelope already signals it) | ~5% per response |
| Logcat compression | Strip timestamps, deduplicate lines, tail-truncate to 8,000 chars | 30-60% on logcat |
| Meta-tools always present | `android_search_tools` and `android_describe_tools` always registered | N/A (additive) |

## Optimizations Detail

### 1. Compact UI Tree (--no-compact-tree to disable)

`android_get_ui_tree` returns a tabular text format instead of verbose JSON:

```
IDX | resource_id | text | desc | flags | bounds
0 | btn_login | Login | | c | [100,200,300,260]
1 | edit_email | | Email | f | [50,300,400,350]
```

Flags: `c`=clickable, `f`=focusable, `s`=scrollable, `k`=checkable

An `index_map` JSON object maps indices to element UUIDs for action resolution.

**Savings:** A 50-element screen drops from ~3,000 tokens (verbose JSON) to ~800 tokens (tabular).

### 2. Smart Element Filtering (--no-filter-elements to disable)

`android_get_ui_tree` defaults to `filter: "interactive"`, showing only elements that are clickable, focusable, scrollable, checkable, or have text/descriptions. Override per-call with `filter: "all"` or `filter: "text"`.

**Savings:** Typical Android screens have 200+ nodes but only 20-40 interactive elements (80% reduction).

### 3. Compact Bounds (--no-compact-bounds to disable)

Element bounds use array format `[left, top, right, bottom]` instead of object `{"left": ..., "top": ..., "right": ..., "bottom": ...}`.

**Savings:** ~15 tokens per element × 30 elements = ~450 tokens per tree response.

### 4. Omit Empty Fields (always on)

Element JSON omits:
- Empty strings (`resource_id`, `text`, `content_description`)
- Common layout class names (`android.view.View`, `android.widget.FrameLayout`, etc.)
- False boolean flags (`clickable`, `focusable`, `scrollable`, `checkable`)
- Zero/empty `semantic_type`

**Savings:** ~10-15 tokens per element for typical UI elements.

### 5. Strip Success Field (always on)

Removes redundant `"success": true` from all tool responses. The MCP envelope already signals success/failure. Error responses still include `"success": false` where meaningful.

**Savings:** ~5 tokens × every response.

### 6. Tool Consolidation (--no-consolidate to disable)

Removes 4 redundant tools from the MCP tool listing:
- `android_fling` → use `android_swipe` with `duration_ms < 200`
- `android_pull_to_refresh` → use `android_swipe` (top to middle)
- `android_dismiss_keyboard` → use `android_global_action("back")`
- `android_get_foreground_app` → included in `android_get_screen_context`

**Savings:** ~1,000 tokens of tool definition overhead per API call.

### 7. Logcat Compression (always on)

`android_capture_logcat` automatically:
- Strips timestamp/PID/TID prefixes from logcat lines
- Deduplicates consecutive identical lines (shows `(xN)` count)
- Truncates to 8,000 chars keeping most recent lines (tail)
- Reports `original_chars` and `compressed_chars` in response

**Savings:** 30-60% on logcat output depending on verbosity.

### 8. Dynamic Tool Discovery (always available)

Two meta-tools are always registered for agents that want to discover tools at runtime:
- `android_search_tools(query, category?)` — keyword search across tool catalog (43 tools, 6 categories)
- `android_describe_tools(tools[])` — get descriptions for specific tools

Categories: `observe`, `act`, `manage`, `device`, `wait`, `test`, `meta`

## Combined Impact

For a typical automation session with `android_get_ui_tree` + `android_find_elements` + action tools:

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Tool definitions (per call) | ~9,860 tokens | ~5,860 tokens | 40% |
| get_ui_tree response (50 elements) | ~3,000 tokens | ~800 tokens | 73% |
| find_elements response (5 matches) | ~400 tokens | ~150 tokens | 62% |
| Logcat (100 lines) | ~4,000 chars | ~2,000 chars | 50% |
| Per action response | ~25 tokens | ~10 tokens | 60% |

**Overall session impact: 40-70% token reduction** depending on operation mix.

## CLI Reference

```bash
# Default (all optimizations ON)
neuralbridge-mcp --auto-discover

# Disable specific optimizations
neuralbridge-mcp --no-compact-tree --no-filter-elements

# Disable all configurable optimizations (verbose mode)
neuralbridge-mcp --no-compact-tree --no-filter-elements --no-compact-bounds --no-consolidate
```
