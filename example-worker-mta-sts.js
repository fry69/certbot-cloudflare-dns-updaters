export default {
	async fetch(request, env, ctx) {
		const url = new URL(request.url);
		const path = url.pathname;

		// Define the allowed paths
		const allowedPaths = ['/.well-known/mta-sts.txt'];

		// Check if the path is allowed
		if (allowedPaths.includes(path)) {
			let reply = 'version: STSv1\n';
			reply += 'mode: enforce\n';
			reply += 'mx: mx1.example.com\n';
			reply += 'mx: mx2.example.com\n';
			reply += 'max_age: 604800\n';
			return new Response(reply, {
				headers: {
					"content-type": "text/plain",
				},
			});
		} else {
			// Serve a 404 response
			return new Response('Not Found', { status: 404 });
		}
	},
};
