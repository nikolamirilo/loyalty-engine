This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Routes

Everything under `app/(protected)` is the admin console and needs a signed-in
session (see `proxy.ts`). Two routes are public:

- `/login` - the console sign-in.
- `/verify` - where DOI verification emails of `type: "page"` land. The API mails
  the member `{CLIENT_BASE_URL}/verify?memberId=<id>&code=<code>`; the page reads
  that pair from the query string and a single button posts it to the API's
  `/doi/verify` through a Server Action, so the API token stays on the server.
  Members opening it are not admins and never will be, which is why it sits
  outside `(protected)` and is exempted in `proxy.ts`.

  Set `CLIENT_BASE_URL` on the **API** to this app's public base URL, otherwise a
  `type: "page"` trigger has no link to send and answers `500`.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
