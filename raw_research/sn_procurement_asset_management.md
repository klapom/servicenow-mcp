---
source_type: process
topics:
  - procurement
  - purchase order
  - asset management
  - hardware asset management
  - stockroom
  - receiving
  - alm_asset
  - proc_po
  - cmdb_hardware_product_model
  - transfer order
  - ham
  - ham pro
  - model category
---

# Procurement Operations & Asset Management

## Overview

ServiceNow's **Procurement Operations** module is the engine that turns business demand for hardware (and consumables) into ordered, received, deployed, and ultimately retired IT assets and configuration items. It sits at the intersection of three large platforms: **IT Service Management (ITSM)** (where the demand is captured as a Service Catalog request), **IT Asset Management / Hardware Asset Management (ITAM/HAM)** (where the financial and lifecycle record of the asset is kept), and the **CMDB** (where the operational, relationship-aware representation of the device is stored). The module is activated by the "Procurement" plugin (`com.snc.procurement`) and is shipped with every ITSM/ITAM bundle; HAM Pro layers additional Flow Designer flows, mobile receiving, model normalization, and a Hardware Asset Manager Workspace on top.

The core promise of the module is that a single purchase order (`proc_po`) drives an auditable chain: the PO is approved, sent to a vendor, items arrive at a stockroom, a receiving slip (`proc_rec_slip`) is created against the PO, and — driven by Business Rules and the **Model Category** record — one `alm_asset` (or `alm_hardware`) record per received unit is created automatically. If the model category also references a CI class, a matching `cmdb_ci_*` record is generated and bidirectionally synchronized with the asset.

The module is also the canonical sourcing path for `sc_request` / `sc_req_item` records: when a catalog item references a Model, the "Can request be sourced" Business Rule allows the Procurement Manager to fulfill the line either by issuing a new PO, consolidating into an existing PO, or transferring from a stockroom via `alm_transfer_order`. This is what enables the end-to-end "Request → Order → Receive → Deploy → Use → Retire" lifecycle that ServiceNow ITAM is built around.

## Module Architecture

ServiceNow ships three overlapping layers; understanding which one is in play is critical because the same table names (`proc_po`, `alm_asset`) appear in all three but with different Flow Designer flows, UI Pages, and Business Rules layered on top.

| Layer | Plugin | Scope | Key additions |
|---|---|---|---|
| **Procurement (core)** | `com.snc.procurement` | Free with ITSM/ITAM. Manual PO creation, basic approval at $1,000 threshold, manual receiving slip. | Tables: `proc_po`, `proc_po_item`, `proc_rec_slip`, `proc_rec_slip_item`, `proc_definition`. |
| **Core Asset Management** | `com.snc.asset_management` | Manages `alm_asset` and `alm_hardware`, stockrooms, transfer orders. | Asset/CI sync, model categories, stockroom transfers. |
| **Hardware Asset Management (HAM) Standard / Pro** | `sn_hamp` (Pro) | Subscription product. Pro adds Flow Designer workflows for the whole lifecycle, model normalization, Hardware Asset Manager Workspace, Agent Mobile barcode scanning, disposal certificates, GenAI sourcing/repair agents. | Pro is a strict superset; Standard is closer to core. |
| **Sourcing & Procurement Operations (SPO)** | Source-to-Pay app | Enterprise procurement: requisitions, sourcing events, contract-driven POs, vendor portals. Distinct from the IT-focused Procurement plugin and typically used outside IT. | Separate `proc_*` workflows under `source-to-pay-operations` doc bundle. |

For Phoenix-scale IT use cases, the relevant stack is **Procurement + Core Asset Management + (optionally) HAM Pro**. The SPO/Source-to-Pay module is a separate enterprise procurement product and uses overlapping but distinct workflows.

## Core Tables

### proc_po — Purchase Order

The Purchase Order is the parent record. It extends `task` (so it inherits `number`, `state`, `assigned_to`, `short_description`, etc., from `task`) but the **`state` field is overridden** with procurement-specific choices.

**Key fields:**

| Field | Type | Notes |
|---|---|---|
| `number` | String | Auto-numbered `PO0001000` |
| `state` | Choice | See state machine below |
| `vendor` | Reference (core_company) | Vendor receiving the PO. Read-only after Order is issued (KB0758034). |
| `ship_to` | Reference (alm_stockroom) | Stockroom where goods will be delivered |
| `requested_by` | Reference (sys_user) | Procurement Manager / requester |
| `requested_delivery` | Date | Target delivery date |
| `expected_delivery` | Date | Vendor-confirmed date |
| `ordered_on` | Date | Stamped when state moves to Ordered |
| `total_cost` | Currency | Rollup of `proc_po_item.unit_cost * quantity` |
| `request` | Reference (sc_request) | Originating service catalog request, if sourced from one |
| `short_description` | String | From `task` |
| `description` | String | From `task` |

**State machine (`proc_po.state`):**

```
[Draft] --submit--> [Ready] --approval--> [Pending Approval]
                                              |
                                          approved
                                              v
                                          [Approved] --click "Order"--> [Ordered]
                                              |                              |
                                              | rejected                     | items arrive,
                                              v                              | receiving slip created
                                          [Cancelled]                        v
                                                                         [Partially Received]
                                                                              |
                                                                              | all items received
                                                                              v
                                                                          [Received] --close--> [Closed Complete]
                                                                                                       |
                                                                                                       +--> [Closed Incomplete]
                                                                                                       +--> [Closed Skipped]
```

Out-of-the-box, **items under $1,000 are auto-approved**, items above trigger a manual approval (configurable via "Procurement approval" workflow). The "Order" UI Action transitions Approved → Ordered and stamps `ordered_on`; this is also the action that, with the HAM "create assets at order time" option enabled, can pre-create `alm_asset` records in the **On Order** state.

### proc_po_item — Purchase Order Line Item

The child of `proc_po`. Each line represents N units of one product model at a unit cost. Extends `task`.

**Key fields:**

| Field | Type | Notes |
|---|---|---|
| `purchase_order` | Reference (proc_po) | Parent |
| `model` | Reference (cmdb_model) | Product model (typically `cmdb_hardware_product_model` subclass) |
| `model_category` | Reference (cmdb_model_category) | Drives which asset class & CI class are auto-created |
| `vendor_catalog_item` | Reference (pc_vendor_cat_item) | Optional vendor-specific SKU/price linkage |
| `quantity` | Integer | Total ordered |
| `received_quantity` | Integer | Rolled up from `proc_rec_slip_item` records |
| `unit_cost` | Currency | Per-unit price |
| `request_line` | Reference (sc_req_item) | Originating RITM if sourced from catalog |
| `stockroom` | Reference (alm_stockroom) | Override of header `ship_to` per line |
| `expected_delivery` | Date | Per-line override |

When `received_quantity == quantity` for every line, the parent `proc_po` is eligible to transition to **Received**. Each unit that is received creates exactly one `alm_asset` (or appropriate subclass) record — this is the core auto-creation contract.

### proc_rec_slip — Receiving Slip

Header record for a physical receipt event at a stockroom. Created when goods arrive against an `Ordered` PO. Extends `task`.

**Key fields:**

| Field | Type | Notes |
|---|---|---|
| `number` | String | `REC0001000` |
| `purchase_order` | Reference (proc_po) | PO being received against |
| `stockroom` | Reference (alm_stockroom) | Physical receiving location |
| `received_by` | Reference (sys_user) | Person logging the receipt |
| `state` | Choice | Draft → Received |
| `arrival_date` | DateTime | When goods physically arrived |

A receiving slip can be **partial** — i.e. only some of the units on a line are received. The slip can be saved, leaving the PO in "Partially Received" until subsequent slips close the remainder.

### proc_rec_slip_item — Receiving Slip Line Item

Records *how many* units of one `proc_po_item` line are being received in this slip.

**Key fields:**

| Field | Type | Notes |
|---|---|---|
| `receiving_slip` | Reference (proc_rec_slip) | Parent |
| `po_line_item` | Reference (proc_po_item) | The PO line being received |
| `received_quantity` | Integer | Units received in *this* slip |
| `asset` | Reference (alm_asset) | Populated for the asset(s) created during this receipt — typically with the *first* asset; a related list shows all created assets |
| `condition` | Choice | Optional condition (Good / Damaged / etc.) |

**Trigger behavior:** On insert/approval of `proc_rec_slip_item`, a Business Rule increments `proc_po_item.received_quantity` and — for each unit received — calls the `AssetandCI` script include to create one `alm_asset` record. When `received_quantity == quantity` on every PO line, the PO state auto-transitions to **Received**.

### alm_asset — Asset (financial / lifecycle record)

The canonical "we own this thing" record. `alm_asset` is the base; physical IT devices live in the `alm_hardware` subclass.

**Key fields:**

| Field | Type | Notes |
|---|---|---|
| `asset_tag` | String | Internal tag; commonly the primary business key |
| `serial_number` | String | Vendor serial |
| `model` | Reference (cmdb_model) | Product model |
| `model_category` | Reference (cmdb_model_category) | Drives CI class for auto-create |
| `install_status` | Choice (integer-backed) | **State** — see state machine |
| `substatus` | Choice | Sub-reason within state (e.g. In Stock → Defective) |
| `ci` | Reference (cmdb_ci) | Linked CI (auto-populated by `AssetAndCISynchronizer`) |
| `assigned_to` | Reference (sys_user) | When `install_status = In Use` |
| `stockroom` | Reference (alm_stockroom) | When `install_status = In Stock` |
| `location` | Reference (cmn_location) | Physical location |
| `purchase_date` | Date | From PO |
| `cost` | Currency | From `proc_po_item.unit_cost` |
| `vendor` | Reference (core_company) | From PO |
| `po_number` | Reference (proc_po) | Source PO |
| `warranty_expiration` | Date | |
| `lease_id` | Reference | If leased |

### alm_hardware — Hardware Asset

Subclass of `alm_asset` for physical IT devices (computers, network gear, mobile, servers). Same field set plus hardware-specific fields like `mac_address`, `ram`, `cpu_count` that mirror what discovery would populate on the CI side. Most procurement-driven receipts land in `alm_hardware` (not the base `alm_asset`) because the model category points there.

### alm_stockroom — Stockroom

A physical or logical location where assets are held. Each stockroom has a manager and a type (e.g. Main, In-Transit, Disposal, Repair).

**Key fields:** `name`, `location` (cmn_location), `manager` (sys_user), `stockroom_type`, `parent` (for hierarchical stockrooms). Related list `alm_user_stockroom` defines users' default stockrooms for self-service requests. **Stock Rules** (`alm_stock_rule`) define thresholds: when on-hand for a model drops below `min`, auto-create a transfer order or PO to top up.

### alm_transfer_order & alm_transfer_order_line — Transfer Order

Moves assets between stockrooms without going through a vendor PO.

**`alm_transfer_order` key fields:** `number` (TRF…), `from_stockroom`, `to_stockroom`, `state` (Draft → Requested → Shipment Preparation → Fully Shipped → Received → Delivered), `requested_by`, `request` (originating sc_request if any).

**`alm_transfer_order_line` key fields:** `transfer_order`, `asset` (specific `alm_asset` being moved) or `model`+`quantity` (when sourcing by model), `state`. When a line's "Ship task" closes, the linked asset's `install_status` flips to **In Transit**; on receipt at the destination, the stockroom is updated and the asset returns to **In Stock**.

### cmdb_hardware_product_model — Hardware Product Model

The catalog of "what could be ordered" — every PO line references a model from here. Extends `cmdb_model`.

**Key fields:** `name`, `model_number`, `manufacturer` (core_company), `cmdb_model_category` (back-reference is `category` on cmdb_model), `product_url`, `weight`, `power_consumption`, `rack_units` (for rack-mount), `cpu_*`, `memory_*`, `disk_*` spec fields.

**Vendor catalog imports:** Vendors like HP, Dell, Lenovo, Cisco distribute model catalogs that can be ingested via Import Sets, the Common Service Data Model (CSDM) content service, or Discovery normalization. The well-known pain point (per ServiceNow Community KB0725174 and many threads): third-party feeds frequently put the *model number* into the *name* field, breaking matching. The matching key used internally by `AssetandCI` and Discovery is the triple **(manufacturer, model name, model number)**. ServiceNow's **Content Service for Normalization** (part of HAM Pro and Software Asset Management) provides curated mappings for major manufacturers — but it requires you to "send in" any models it doesn't already know, which generates manual normalization tickets if your discovery data is dirty.

### cmdb_model_category — Model Category

Tiny but pivotal table. Each row binds an *asset class* to a *CI class* and to a *bundle* flag.

**Key fields:**

| Field | Notes |
|---|---|
| `name` | e.g. "Server", "Computer", "Network Gear" |
| `asset_class` | Sys-name of the asset table to create (e.g. `alm_hardware`) |
| `cmdb_ci_class` | Sys-name of the CI table to create (e.g. `cmdb_ci_server`) — **cannot be changed after creation** |
| `enforce_verification` | When true, prevents auto-create of asset when CI is created |
| `bundle` | Indicates the model is a bundle of components |
| `show_in` | Controls whether the category appears in Asset, CI, or both forms |

**Out-of-box categories** include: Computer, Server, Network Gear, Storage Device, Phone, Printer, Rack, Monitor, Consumable, Software License, plus four resource categories (End user computer, Mobile device, Network Gear, Server) that drive HAM Pro licensing math.

### proc_definition — Procurement Definition

An optional record used in Sourcing & Procurement Operations to define a procurement catalog item's behavior (approval rules, default vendor, default stockroom). In the IT Procurement plugin this table is sparsely populated; most logic lives in the Business Rule layer instead. SPO uses it more heavily for buyer-driven catalogs.

## End-to-End Flow: Order → CI

Realistic example: **Procurement Manager orders 10 × HP ProLiant DL380 Gen11 servers.**

```
1.  USER REQUESTS
    sc_req_item created from catalog item "Standard Rack Server"
    catalog item references model = cmdb_hardware_product_model:HP DL380 Gen11
    quantity = 10
        |
        v
2.  SOURCING
    Procurement Manager opens the Source Request UI Page
    Business Rule "Can request be sourced" verifies the line has a model
    Manager clicks "Create Purchase Order"
        |
        v
3.  proc_po (state=Draft) created
        + proc_po_item (model=HP DL380 G11, quantity=10, unit_cost=$8,500)
        + linked back to sc_req_item via request_line
        |
        v
4.  Submit -> state=Ready -> Approval Workflow
    Total $85,000 > $1,000 threshold -> manual approval
    Approver approves -> state=Approved
        |
        v
5.  Procurement Manager clicks "Order"
    state -> Ordered
    ordered_on stamped
    Vendor receives PO (email notification via sysevent)
    [Optionally: 10 alm_hardware records created NOW in install_status=On Order]
        |
        v
6.  GOODS ARRIVE at Stockroom "DC1-Receiving"
    User creates proc_rec_slip
        + proc_rec_slip_item (po_line_item=line1, received_quantity=10)
        |
        v
7.  ON RECEIPT (Business Rules fire):
    a) proc_po_item.received_quantity += 10
    b) AssetandCI.createAssets() called 10 times
       -> 10 alm_hardware rows inserted
          - model = HP DL380 G11
          - model_category = "Server" (-> cmdb_ci_server CI class)
          - install_status = In Stock
          - stockroom = DC1-Receiving
          - po_number = PO0001000
          - cost = $8,500
          - asset_tag auto-generated (or scanned in HAM Pro mobile)
    c) For each alm_hardware, BR "Create CI on insert" fires
       -> 10 cmdb_ci_server CI records created, ci field on asset populated
    d) AssetAndCISynchronizer keeps name/serial/status in sync
    e) When all PO lines fully received, proc_po.state -> Received
        |
        v
8.  DEPLOYMENT
    Asset assigned to user/location -> install_status = In Use
    Synchronizer flips cmdb_ci_server.install_status to "Installed"
    Catalog tasks for the RITM close, RITM closes, REQ closes
        |
        v
9.  LIFECYCLE
    Discovery picks up the running server, enriches the cmdb_ci_server
    Asset and CI remain linked via asset.ci <-> cmdb_ci.asset_tag
```

## Asset State Machine

`alm_asset.install_status` is integer-backed; labels vary slightly across releases, but the canonical OOTB values are below. **Exact numeric codes can vary by instance** — they live in `sys_choice` for table `alm_asset`, element `install_status` — and ServiceNow has added/renamed states across releases (e.g. "Consumed" was added/renamed when CSDM Life Cycle was enabled, per KB1433675).

| Value (typical) | Label | Meaning | Triggered by |
|---|---|---|---|
| 6 | On Order | Pre-created from PO Order action | "Create assets at order time" option |
| 2 | In Stock | Sitting in a stockroom, unassigned | Receiving slip creation |
| 10 | In Transit | Being moved via transfer order | Transfer order ship task closes |
| 1 | In Use | Deployed to a user/location | Manual or catalog task closure |
| 3 | In Maintenance | Under repair | Manual / repair workflow |
| 8 | Pending Install | Configured but not yet active | Manual |
| 9 | Pending Repair | Awaiting repair (substate of In Stock often) | Manual |
| 7 | Retired | Lifecycle ended but not yet disposed | Retirement action |
| 100 | Missing | Cannot be located | Audit / manual |
| (varies) | Consumed | One-time-use asset consumed (also used by CSDM Life Cycle) | CSDM flow / consumable rules |

**Substates** add the "why" — e.g. `In Stock → Available`, `In Stock → Reserved`, `In Stock → Defective`, `Retired → Pending Disposal`, `Retired → Disposed`. HAM Pro uses these to fire repair workflows and disposal-certificate generation.

**Transition triggers (summary):**
- **Order PO** → On Order (only if HAM "early create" enabled)
- **Receiving slip created/approved** → In Stock
- **Transfer order ship task closed** → In Transit
- **Transfer order received** → In Stock (new stockroom)
- **Asset assigned to user, or RITM catalog task delivered** → In Use
- **Retirement UI Action** → Retired
- **Disposal certificate recorded (HAM Pro)** → Retired/Disposed

## Auto-Creation Rules

### Asset auto-creation from receiving

Driven by Business Rule **"Create asset on receiving slip approval"** (or equivalent on `proc_rec_slip_item.insert`). Logic:

1. For each `proc_rec_slip_item` line, take `received_quantity` and the linked `proc_po_item.model` / `model_category`.
2. Call `new AssetandCI().createAssets(model_category, quantity, po_item)`.
3. For each unit, insert one record in the `model_category.asset_class` table (typically `alm_hardware`) with:
   - `install_status = In Stock`
   - `stockroom`, `cost`, `vendor`, `po_number`, `purchase_date` copied from the PO
   - `asset_tag` auto-generated by number maintenance, unless overridden
4. Increment `proc_po_item.received_quantity`.
5. If all lines fully received, transition `proc_po` to **Received**.

Exceptions (no asset created): consumable model categories, license/software categories, pre-allocated assets, or PO lines where assets were already pre-created at Order time.

### CI auto-creation from asset

Driven by Business Rule **"Create CI on insert"** on `alm_asset` (and the mirror "Create Asset on insert" on the CI tables). Logic:

1. On asset insert, look up `model_category.cmdb_ci_class`.
2. If non-empty, insert a new record in that CI class.
3. Populate `asset.ci` ← new CI sys_id; populate `cmdb_ci.asset_tag` ← asset's asset_tag.
4. The `AssetAndCISynchronizer` script include then mirrors a curated field list (serial_number, model, name, install_status mapping, location, assigned_to, …) on every future update on either side.

Both directions are gated by the **"Enforce CI Verification"** flag on the model category — when true, the CI side is the "master" and assets are not auto-created from CIs (used in CMDB-master shops).

Both rules ultimately call the **`AssetandCI`** Script Include (note the lowercase `and`) — the canonical reference implementation. The sync direction is governed by **`AssetAndCISynchronizer`** (camelCase and capital `And`).

### Asset pre-creation at order time

A HAM convenience: when an Ordered PO line is for hardware and the model category supports it, a "Create assets" UI link appears on the PO/PO line. Clicking it creates the `alm_asset` records immediately in **On Order** state. This lets receiving teams scan asset tags against pre-existing records rather than creating them at receipt. Their state moves to **In Stock** on the receiving slip event.

## Stockroom & Transfer Workflow

Stockrooms are the spatial anchor for any asset that is not currently in use. The flow:

1. **Stock rules** (`alm_stock_rule`) define `(stockroom, model, min, max)`. When a scheduled job (`Stock Rule Eval`) sees on-hand for a model in a stockroom drop below `min`, it either:
   - Creates a transfer order from another stockroom with surplus, or
   - Creates a purchase order against the model's preferred vendor.
2. **Transfer order request flow:** A user (or system) opens `alm_transfer_order` → adds lines → submits.
3. **Shipment:** A "Ship Task" (catalog task) is created; closing it sets `asset.install_status = In Transit` and `asset.stockroom = (in-transit virtual stockroom)`.
4. **Receipt:** At the destination, "Receive on transfer order line" sets `asset.stockroom = to_stockroom` and `install_status = In Stock`.
5. **Delivery (optional FSM step):** With Field Service Management, a delivery task can carry the asset to the end user; closing that task sets `install_status = In Use`.

Sourcing a catalog request from a stockroom (rather than a PO) is the default behavior when on-hand `>= requested quantity` for the model in the user's default stockroom — this is what `alm_user_stockroom` is for: it tells the sourcing rule "which stockroom does *this* user normally pull from?"

## Integration Points

- **Service Catalog (`sc_request` / `sc_req_item` → `proc_po`)**: The "Source Request" UI Page is the bridge. The Business Rule "Can request be sourced" validates `sc_req_item.cat_item` has a `model`. Sourcing options: new PO, add to existing PO, transfer order from stockroom. The `sc_req_item` is linked to `proc_po_item.request_line`, and catalog tasks for delivery are created only after the PO is received.
- **Change Management (`change_request` ↔ `proc_po`)**: Most shops link via custom reference field `change_request.purchase_order` (or via a related list on the PO). The Change can then gate Order or Receive actions for high-cost hardware.
- **CMDB (`alm_asset.ci` ↔ `cmdb_ci.asset_tag`)**: Bidirectional. The synchronizer keeps the curated field list aligned. Discovery enriches the CI side; the asset side is the financial source of truth.
- **Vendor Management (`core_company` + `ast_contract`)**: Vendor on the PO is a `core_company` with `vendor=true`. Contracts (`ast_contract`) can be referenced from the PO for spend-against-contract reporting. SPO adds full contract-lifecycle on top.
- **Financial Management**: PO `total_cost` rolls into ITAM cost models; receipts feed depreciation schedules on the asset.
- **Procurement notifications**: PO/PO-line notifications fire via `sysevent_register` events (`po.ordered`, `po.received`) and standard notification records.

## Common Customizations & Pain Points

- **Approval threshold ($1,000 OOTB)**: Almost every customer changes this. The threshold lives in the "Procurement approval" Workflow / Flow and in a property; sometimes branched on `cost_center` or `requested_for.department`.
- **Asset tag generation**: Defaults to plain incrementing numbers (`P1000`, `P1001`); most enterprises override with prefixed schemes per category or per site via Number Maintenance + Business Rule overrides.
- **Model normalization**: Vendor catalog imports collide with the (manufacturer, model name, model number) matching key. Symptom: duplicate `cmdb_hardware_product_model` rows for the same physical model with subtly different names (e.g. "ProLiant DL380 Gen11" vs "HP ProLiant DL380 Gen 11"). Remedy: enable Content Service for Normalization (HAM Pro) or maintain a custom matching rule.
- **CI class lock-in**: `cmdb_model_category.cmdb_ci_class` cannot be changed after creation. Teams who pick the wrong CI class end up creating a new model category and migrating assets — painful at scale.
- **Receiving slip without asset auto-create**: Custom Business Rules that suppress auto-create (e.g. for software-license PO lines) often accidentally suppress hardware too — a common defect.
- **Pre-create at Order vs Create at Receive**: Choosing one is an org policy decision. Mixing causes duplicate assets if the receiving team is not aware that 10 On-Order assets already exist for the PO.
- **Stockroom hierarchy**: `parent` is supported but most reports don't roll up by hierarchy out-of-box; teams write custom aggregations.
- **CSDM Life Cycle interactions**: Enabling the CSDM Life Cycle plugin can silently change `install_status` to "Consumed" on hardware assets (KB1433675) — a known landmine when adopting CSDM late.
- **Transfer Order delivery step**: Without FSM, the "Deliver" step requires a UI configuration adjustment; many teams short-circuit by closing the transfer at "Received" and using a separate catalog task for last-mile delivery.
- **Version differences**: Tokyo/Utah → Washington DC → Xanadu → Yokohama → Zurich progressively moved Procurement workflows from classic Workflow Engine to Flow Designer, added the Hardware Asset Manager Workspace (HAM Pro), and refactored the substate model. Field names are stable; UI and flow definitions are not.
- **HAM Standard vs Pro**: Standard gives you `proc_po`, basic receiving, stockrooms. Pro adds: mobile barcode receiving (Agent Mobile), automated model normalization, repair/disposal workflows with certificates, the Workspace, Stockroom Audit, GenAI sourcing/repair agents, and out-of-box Flow Designer flows for every lifecycle phase. The data model (tables, fields) is the same.
- **SPO vs IT Procurement plugin confusion**: Two distinct products both use `proc_*` table names with overlapping but non-identical schemas and workflows; check the plugin set before assuming behavior.

## References

- ServiceNow Docs — [Tables installed with Procurement (Washington DC)](https://www.servicenow.com/docs/r/washingtondc/it-asset-management/procurement/r_TablesProcurement.html)
- ServiceNow Docs — [Procurement purchase order management for assets](https://www.servicenow.com/docs/r/washingtondc/it-asset-management/procurement/c_UseProcurement.html)
- ServiceNow Docs — [Create a Receiving Slip (Yokohama)](https://www.servicenow.com/docs/bundle/yokohama-it-asset-management/page/product/procurement/task/t_CreateAReceivingSlip.html)
- ServiceNow Docs — [Map asset state and CI hardware status (Yokohama)](https://www.servicenow.com/docs/bundle/yokohama-it-asset-management/page/product/asset-management/task/t_CreateAssetandCIHardwareStatusMapping.html)
- ServiceNow Docs — [Manage your stockrooms (HAM)](https://www.servicenow.com/docs/r/it-asset-management/hardware-asset-management/manage-your-stockrooms.html)
- ServiceNow Docs — [Business Rules in Procurement (Utah)](https://docs.servicenow.com/en-US/bundle/utah-it-asset-management/page/product/procurement/reference/r_BusinessRulesProcurement.html)
- ServiceNow Docs — [Hardware model fields (Tokyo)](https://docs.servicenow.com/en-US/bundle/tokyo-it-asset-management/page/product/hardware-asset-management/reference/hardware-model-fields.html)
- ServiceNow Docs — [Transfer orders (Rome)](https://docs.servicenow.com/bundle/rome-it-asset-management/page/product/asset-management/concept/transfer-orders-asset.html)
- ServiceNow Docs — [Sourcing and Procurement Operations / Purchase Order](https://www.servicenow.com/docs/r/source-to-pay-operations/sourcing-and-procurement-operations/purchase-order.html)
- ServiceNow Community — [Quick Start Guide: Procurement request and purchase orders](https://www.servicenow.com/community/ham-articles/quick-start-guide-procurement-request-and-purchase-orders/ta-p/2990536)
- ServiceNow Community — [Assets, CIs and Model Categories: how they work together](https://www.servicenow.com/community/in-other-news/assets-configuration-items-and-model-categories-understanding/ba-p/2279633)
- ServiceNow Community — [Mastering HAM in ServiceNow — Chapter 2 (Zurich)](https://www.servicenow.com/community/ham-articles/mastering-hardware-asset-management-in-servicenow-chapter-2/ta-p/3351555)
- ServiceNow Community — [Core Asset Management vs HAM Pro](https://www.servicenow.com/community/ham-blog/core-asset-management-vs-ham-pro-what-you-actually-get-and-when/ba-p/3518013)
- ServiceNow Community — [Verify numeric values of install_status](https://www.servicenow.com/community/knowledge-managers/verify-numeric-values-of-install-status/m-p/299125) — confirms install_status numeric codes live in `sys_choice` and vary by instance.
- ServiceNow Now Support — [KB0999333: Enable "Create CI on Asset Insert" Business Rule](https://noderegister.service-now.com/kb?id=kb_article_view&sysparm_article=KB0999333)
- ServiceNow Now Support — [KB1433675: Enabling CSDM Life Cycle can change Hardware Asset state to Consumed](https://support.servicenow.com/kb?id=kb_article_view&sysparm_article=KB1433675)
- ServiceNow Now Support — [KB0758034: Cannot edit Vendor field on Purchase Order](https://support.servicenow.com/kb?id=kb_article_view&sysparm_article=KB0758034)
- ServiceNow Now Support — [KB0997015: Product Model, Product Catalog Item, Vendor Catalog Item relationship](https://support.servicenow.com/kb?id=kb_article_view&sysparm_article=KB0997015)
- ServiceNow Now Support — [KB0725174: CMDB Model — best practice mapping during imports](https://support.servicenow.com/kb?id=kb_article_view&sysparm_article=KB0725174)
- ServiceNow Elite — [Procurement (2016 overview, still accurate on workflow shape)](https://www.servicenowelite.com/blog/2016/10/23/procurement)
- ServiceNow Elite — [Asset Management (2016)](https://www.servicenowelite.com/blog/2016/9/22/asset-management)
- ServiceNow Guru — [Overview of ServiceNow Hardware Asset Management](https://servicenowguru.com/hardware-asset-management/overview-of-servicenow-hardware-asset-management/)
- Inmorphis — [HAM vs HAM Pro feature comparison](https://inmorphis.com/insights/blogs/servicenow-hardware-asset-management-understanding-ham-vs-ham-pro)
- Reco.ai — [ServiceNow Asset Management technical guide for IT admins](https://www.reco.ai/hub/servicenow-asset-management)
- Rowan University — [ServiceNow Procurement training manual v1.0 (PDF)](https://irt.rowan.edu/_docs/training/manuals/servicenow-procurement-manual.pdf) — PDF, binary, but is the most cited public end-user training doc for PO lifecycle.
