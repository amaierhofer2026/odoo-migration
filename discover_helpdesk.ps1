# List all helpdesk-related tables in Odoo 18 (OCA helpdesk_mgmt)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Helpdesk Table Discovery" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ============================================================
# 1. Find all helpdesk tables
# ============================================================
Write-Host ""
Write-Host "[1] All helpdesk-related tables..." -ForegroundColor Yellow

$tables = docker exec odoo18-db psql -U odoo -d odoo18_test -c "
SELECT table_name,
       (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name AND table_schema = 'public') as col_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name LIKE '%helpdesk%'
ORDER BY table_name;
" 2>&1
Write-Host $tables

# ============================================================
# 2. Row counts for each helpdesk table
# ============================================================
Write-Host ""
Write-Host "[2] Row counts for each helpdesk table..." -ForegroundColor Yellow

$rows = docker exec odoo18-db psql -U odoo -d odoo18_test -t -c "
SELECT table_name || '=' || (xpath('//row/count/text()', query_to_xml('SELECT COUNT(*) FROM ' || quote_ident(table_name), TRUE, FALSE, '')))[1]::text
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE '%helpdesk%'
ORDER BY table_name;
" 2>&1
Write-Host $rows

# ============================================================
# 3. Also check via pg_class (more reliable, lists ALL relations)
# ============================================================
Write-Host ""
Write-Host "[3] Relations via pg_class..." -ForegroundColor Yellow

$rel = docker exec odoo18-db psql -U odoo -d odoo18_test -c "
SELECT relname, relkind, reltuples::bigint as estimated_rows
FROM pg_class
WHERE relname LIKE '%helpdesk%'
  AND relkind = 'r'
ORDER BY relname;
" 2>&1
Write-Host $rel

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Done" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
