const copyToClipboard = async (text) => {
  await navigator.clipboard.writeText(text);
};

const addCopyButtonToCell = (buttonsContainer, value) => {
  const copyButton = document.createElement("a");
  copyButton.className = "owid-button owid-copy-button fa fa-copy";
  copyButton.title = "Copy to clipboard";
  copyButton.onclick = () => copyToClipboard(value);
  buttonsContainer.append(copyButton);
};

const externalUrlFields = [
  {
    // Chart slug
    colNames: [
      "owid.charts.slug",
      "owid.slug",
      "owid.chartSlug",
      "owid.grapherSlug",
    ],
    fn: (slug) => `https://ourworldindata.org/grapher/${slug}`,
  },
  {
    // Chart ID
    colNames: [
      "owid.charts.id",
      "owid.chartId",
      "owid.grapherId",
      "owid/charts",
    ],
    fn: (id) => `https://owid.cloud/admin/charts/${id}/edit`,
  },
  {
    // Variable ID
    colNames: ["owid.variables.id", "owid.variableId", "owid/variables"],
    fn: (id) => `https://owid.cloud/admin/variables/${id}`,
  },
  {
    // Dataset ID
    colNames: ["owid.datasets.id", "owid.datasetId", "owid/datasets"],
    fn: (id) => `https://owid.cloud/admin/datasets/${id}`,
  },
  {
    // Tag ID
    colNames: ["owid.tags.id", "owid.tagId", "owid/tags"],
    fn: (id) => `https://owid.cloud/admin/tags/${id}`,
  },
  {
    // Post slug
    colNames: ["owid.posts.slug", "owid.posts_gdocs.slug", "owid.postSlug"],
    fn: (slug) => `https://ourworldindata.org/${slug}`,
  },
];

const externalUrlByFieldName = externalUrlFields.reduce(
  (acc, { colNames, fn }) => {
    colNames.forEach((colName) => {
      acc[colName] = fn;
    });
    return acc;
  },
  {}
);

const addExternalUrlButtonToCell = (
  cell,
  buttonsContainer,
  fieldName,
  value
) => {
  let href = externalUrlByFieldName[fieldName]?.(value);

  // If we don't recognize the field name, also try whether this is a foreign key
  // linking out to a table we care about, and try to also add a link to that one
  if (!href) {
    const link = cell.querySelector("a")?.getAttribute("href");
    if (!link || !link.startsWith("/")) return;

    const lastSlashIndex = link.lastIndexOf("/");
    if (lastSlashIndex === -1) return;
    const tableName = link.substring(1, lastSlashIndex);
    const id = link.substring(lastSlashIndex + 1);

    href = externalUrlByFieldName[tableName]?.(id);

    if (!href) return;
  }

  const externalUrlButton = document.createElement("a");
  externalUrlButton.className =
    "owid-button owid-external-url-button fa fa-external-link-alt";
  externalUrlButton.target = "_blank";
  externalUrlButton.rel = "noopener noreferrer";
  externalUrlButton.title = "Open in new tab";
  externalUrlButton.href = href;
  buttonsContainer.appendChild(externalUrlButton);
};

const wrapInDetailsElement = (element) => {
  const detail = document.createElement("details");
  detail.className = "owid-detail";
  element.parentNode.insertBefore(detail, element);
  detail.appendChild(element);
};

let databaseName;
let tableName;
const body = document.body;
body.classList.forEach((className) => {
  if (className.startsWith("db-")) databaseName = className.replace("db-", "");
  else if (className.startsWith("table-"))
    tableName = className.replace("table-", "");
});

const cells = document.querySelectorAll("table.rows-and-columns td");
cells.forEach((cell) => {
  const value = cell.innerText;
  if (!value?.trim?.()) return;

  // Add "owid-buttons" container for any buttons
  const buttonsContainer = document.createElement("div");
  buttonsContainer.className = "owid-buttons";
  cell.appendChild(buttonsContainer);

  // Add a copy button
  addCopyButtonToCell(buttonsContainer, value);

  // Add an external URL button, linking to the grapher/admin etc.
  let colName;
  cell.classList.forEach((className) => {
    if (className.startsWith("col-")) colName = className.replace("col-", "");
  });

  const fieldName = [databaseName, tableName, colName]
    .filter((f) => f)
    .join(".");
  addExternalUrlButtonToCell(cell, buttonsContainer, fieldName, value);

  // Wrap config JSON in a <details> tag
  if (cell.classList.contains("col-config")) {
    const pre = cell.querySelector("pre");
    if (pre) wrapInDetailsElement(pre);
  }
});
