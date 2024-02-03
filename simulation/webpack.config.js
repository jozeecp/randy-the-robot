const path = require("path");

module.exports = {
    // Entry point of the application
    entry: "./src/main.js",

    // Output configuration
    output: {
        path: path.resolve(__dirname, "dist"),
        filename: "bundle.js",
    },

    // Development server configuration
    devServer: {
        static: {
            directory: path.join(__dirname, "dist"),
        },
        compress: true,
        port: 9000,
        allowedHosts: "all",

        headers: {
            // 'X-Frame-Options': 'sameorigin',
            "Access-Control-Allow-Origin": "*", // Allows all origins
            "Access-Control-Allow-Methods":
                "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers":
                "X-Requested-With, content-type, Authorization",
            // OR if you want to allow embedding from any origin:
            // 'X-Frame-Options': 'ALLOW-FROM http://edgebox1:',
            // AND/OR set Content-Security-Policy header
            // 'Content-Security-Policy': "frame-ancestors 'self' http://your-node-red-dashboard-origin"
        },
    },

    // Module rules (for loaders)
    module: {
        rules: [
            {
                // Babel loader configuration
                test: /\.m?js$/,
                exclude: /(node_modules|bower_components)/,
                use: {
                    loader: "babel-loader",
                    options: {
                        presets: ["@babel/preset-env"],
                    },
                },
            },
        ],
    },

    // Development mode
    mode: "development",

    // Source map for debugging
    devtool: "inline-source-map",
};
