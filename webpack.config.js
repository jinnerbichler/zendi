// noinspection NodeJsCodingAssistanceForCoreModules
const path = require('path');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const wepback = require('webpack');

// ------------------------------------------------------------------
//                    Create Plugins
// ------------------------------------------------------------------
const extractPlugin = new ExtractTextPlugin({
    filename: 'main.css'
});
// noinspection JSUnresolvedFunction
const providePlugin = new wepback.ProvidePlugin({
    $: 'jquery',
    jQuery: 'jquery',
    Materialize: 'materialize-css',
});
const cleanPlugin = new CleanWebpackPlugin(['wallet/static/wallet']);
const copyFilesPlugin = new CopyWebpackPlugin([{
    // copy all favicon data
    from: 'assets/img/favicons',
    to: 'img/favicons'
}, {
    // copy dependencies of theme
    from: 'assets/theme',
    to: 'theme'
}]);

// ------------------------------------------------------------------
//                    Configure Webpack
// ------------------------------------------------------------------
module.exports = {
    entry: ['whatwg-fetch', './assets/js/app.js'],
    output: {
        path: path.resolve(__dirname, 'wallet/static/wallet'),
        filename: 'bundle.js',
        libraryTarget: 'var',
        library: 'EntryPoint'
        // publicPath: '/wallet/static/wallet'
        // libraryTarget: 'var',
        // library: 'Bundle'
    },
    module: {
        rules: [
            {
                // ------------------------------------------------------------------
                //                    Load Fonts
                // ------------------------------------------------------------------
                test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                use: [{
                    loader: 'url-loader',
                    options: {
                        name: '[name].[ext]',
                        outputPath: 'font/',
                        limit: 80000,
                    }
                }]
            }, {
                // ------------------------------------------------------------------
                //                    Load Vector Graphics
                // ------------------------------------------------------------------
                test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                loader: 'file-loader'
            }, {
                // ------------------------------------------------------------------
                //                    Load Javascript
                // ------------------------------------------------------------------
                test: /\.js$/,
                use: [{
                    loader: 'babel-loader',
                    options: {
                        presets: ['es2015']
                    }
                }]
            }, {
                // ------------------------------------------------------------------
                //                    Load SCSS Styles
                // ------------------------------------------------------------------
                test: /\.scss$/,
                use: extractPlugin.extract({
                    use: ['css-loader', 'sass-loader']
                }),
                exclude: ['assets/theme/']
            }, {
                // ------------------------------------------------------------------
                //                    Load Images
                // ------------------------------------------------------------------
                test: /\.(jpg|png)$/,
                use: [{
                    loader: 'file-loader',
                    options: {
                        name: '[name].[ext]',
                        outputPath: 'img/',
                    }
                }]
            }]
    },
    plugins: [
        providePlugin,
        extractPlugin,
        cleanPlugin,
        copyFilesPlugin]
};